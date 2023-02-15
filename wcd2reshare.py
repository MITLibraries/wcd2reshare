import logging
import os
import re
import typing
import urllib.parse

import requests
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


def query_formatter(args: dict) -> dict:
    """Transforms a dictionary of OpenURL request params to a dict of search
    strings formatted for BorrowDirect / ReShare vuFind UI.

    """

    searchStrings = {}
    if rft_id := args.get("rft_id"):
        # we expect the rft_id param to contain an 8 or 9 digit oclc number preceeded
        # by some stuff we don't care about
        pattern = re.compile("info%3Aoclcnum%2F([0-9]{8,9})")
        # if we encounter the expected pattern extract the oclc number
        # from the first capture group
        if oclc_num := pattern.match(rft_id):
            searchStrings["oclc"] = [
                ("type", "oclc_num"),
                ("lookfor", oclc_num.group(1)),
            ]

    if isbn := args.get("rft.isbn"):
        searchStrings["isbn"] = [("type", "ISN"), ("lookfor", isbn)]

    if title := (
        args.get("rft.title")
        or args.get("rft.btitle")
        or args.get("rft.ctitle")
        or args.get("rft.jtitle")
    ):
        aulast = args.get("rft.aulast")
        searchStrings["title"] = buildTitleSearchString(title, aulast)
    # urlencode the search strings
    encodedSearchStrings = {
        k: urllib.parse.urlencode(v) for k, v, in searchStrings.items()
    }
    return encodedSearchStrings


def buildTitleSearchString(title: str, aulast: typing.Optional[str]) -> list:
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


def selectSearchStrategy(searchStrings: dict) -> str:
    """takes a dict of search strings and checks whether each search
    string returns any results. Returns the first successful search string.

    Searches are tried in a specific order from most specific to least
    specific
    """

    if query_string := searchStrings.get("oclc"):
        if searchHasResults(query_string):
            return query_string

    if query_string := searchStrings.get("isbn"):
        if searchHasResults(query_string):
            return query_string

    if query_string := searchStrings.get("title"):
        if searchHasResults(query_string):
            return query_string

    return ""


def searchHasResults(searchString: str) -> bool:
    """check whether VuFind API returns any records for a given search string"""
    vuFind_API = "https://borrowdirect.reshare.indexdata.com/api/v1/search?"
    r = requests.get(vuFind_API + searchString)
    body = r.json()
    if body.get("resultCount"):
        return True
    else:
        return False


def lambda_handler(event: dict, context: dict) -> dict:
    """Extracts query string parameters (if any exist) from incoming lambda function URL
    request. If there are query string parameters, try to build query string for
    Reshare / Vufind. Return an object representing an HTTP redirect response to
    ReShare / Vufind, using the query string if one was built.
    """

    if env is None:
        raise ValueError("WORKSPACE environment variable is required")

    location = "https://borrowdirect.reshare.indexdata.com/Search/Results?"
    query_string = ""
    if args := event.get("queryStringParameters"):
        query_string = selectSearchStrategy(query_formatter(args))
        location = location + query_string

    response = {
        "headers": {"Location": location},
        "statusCode": 307,
    }
    return response
