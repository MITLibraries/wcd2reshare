import logging
import os
import urllib.parse

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
env = os.getenv("WORKSPACE")
if sentry_dsn := os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=env,
        integrations=[
            AwsLambdaIntegration(),
        ],
    )
    logger.info("Sentry DSN found, exceptions will be sent to Sentry with env=%s", env)


def query_formatter(args: dict) -> str:
    """Transforms a dictionary of OpenURL request params to a string of search
    params formatted for BorrowDirect / ReShare vuFind UI.

    Logic is:
     if isbn
       use isbn and nothing else
     else if any of the 4 titles exist:
       use the title that exists in this preferential order
          title, btitle, ctitle, jtitle
          nested condition of if aulast include that as well"""

    searchString = []
    if isbn := args.get("rft.isbn"):
        searchString = [("type", "ISN"), ("lookfor", isbn)]
        return urllib.parse.urlencode(searchString)

    if title := (
        args.get("rft.title")
        or args.get("rft.btitle")
        or args.get("rft.ctitle")
        or args.get("rft.jtitle")
    ):
        aulast = args.get("rft.aulast")
        searchString = buildSearchString(title, aulast)
        return urllib.parse.urlencode(searchString)

    # if nothing matches, just return. no search will be done
    return ""


def buildSearchString(title: str, aulast: str = None) -> list:
    """Takes title and aulast (author last name) values from openURL params and builds
    the correct search string syntax for VuFind. If aulast is None, only a title search
    is built. If an aulast is supplied, a combined title / author search is built.
    """
    result = [("type", "title"), ("lookfor", title)]
    if aulast:
        result = [
            ("join", "AND"),
            ("type0[]", "title"),
            ("lookfor0[]", title),
            ("type0[]", "author"),
            ("lookfor0[]", aulast),
        ]
    return result


def lambda_handler(event: dict, context: dict) -> dict:
    """Extracts query string parameters (if any exist) from incoming lambda function URL
    request. If there are query string parameters, try to build query string for
    Reshare / Vufind. Return an object representing an HTTP redirect response to
    ReShare / Vufind, using the query string if one was built.
    """

    if env is None:
        raise ValueError("WORKSPACE environment variable is required")

    location = "https://borrowdirect.reshare.indexdata.com/Search/Results?"

    if args := event.get("queryStringParameters"):
        location = location + query_formatter(args)
    response = {
        "headers": {"Location": location},
        "statusCode": 307,
    }
    return response
