import logging
import os
import re
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
    """Reformat openURL to vufind search strings.

    Transforms a dictionary of OpenURL request params to a dict of search strings for
    BorrowDirect / ReShare vuFind UI.
    """
    search_strings = {}
    if rft_id := args.get("rft_id"):
        # we expect the rft_id param to contain an 8 or 9 digit oclc number preceeded
        # by some stuff we don't care about
        pattern = re.compile("info%3Aoclcnum%2F([0-9]{8,9})")
        # if we encounter the expected pattern extract the oclc number
        # from the first capture group
        if oclc_num := pattern.match(rft_id):
            search_strings["oclc"] = [
                ("type", "oclc_num"),
                ("lookfor", oclc_num.group(1)),
            ]

    if isbn := args.get("rft.isbn"):
        search_strings["isbn"] = [("type", "ISN"), ("lookfor", isbn)]

    if title := (
        args.get("rft.title")
        or args.get("rft.btitle")
        or args.get("rft.ctitle")
        or args.get("rft.jtitle")
    ):
        aulast = args.get("rft.aulast")
        search_strings["title"] = build_title_search_string(title, aulast)
    # urlencode the search strings
    return {k: urllib.parse.urlencode(v) for k, v in search_strings.items()}


def build_title_search_string(title: str, aulast: str | None) -> list:
    """Build a title search string for VuFind.

    Takes title and aulast (author last name) values from openURL params and builds
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


def select_search_strategy(search_strings: dict) -> str:
    """Select the VuFind search strategy.

    takes a dict of search strings and checks whether each search
    string returns any results. Returns the first successful search string.

    Searches are tried in a specific order from most specific to least
    specific
    """
    if (query_string := search_strings.get("oclc")) and search_has_results(query_string):
        return query_string

    if (query_string := search_strings.get("isbn")) and search_has_results(query_string):
        return query_string

    if (query_string := search_strings.get("title")) and search_has_results(query_string):
        return query_string

    return ""


def search_has_results(search_string: str) -> bool:
    """Check whether VuFind API returns any records for a given search string."""
    vufind_api = "https://borrowdirect.reshare.indexdata.com/api/v1/search?"
    r = requests.get(vufind_api + search_string, timeout=10)
    body = r.json()
    return bool(body.get("resultCount"))


def lambda_handler(event: dict, _context: object) -> dict:
    """Handle incoming requests to the lambda function.

    Extracts query string parameters (if any exist) from incoming lambda function URL
    request. If there are query string parameters, try to build query string for
    Reshare / Vufind. Return an object representing an HTTP redirect response to
    ReShare / Vufind, using the query string if one was built.
    """
    if env is None:
        error_message = "WORKSPACE environment variable is required"
        raise ValueError(error_message)

    location = "https://borrowdirect.reshare.indexdata.com/Search/Results?"
    query_string = ""
    if args := event.get("queryStringParameters"):
        query_string = select_search_strategy(query_formatter(args))
        location = location + query_string

    return {
        "headers": {"Location": location},
        "statusCode": 307,
    }
