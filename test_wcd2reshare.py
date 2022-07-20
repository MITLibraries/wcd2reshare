import pytest

import wcd2reshare


@pytest.fixture
def baseURL():
    return "https://borrowdirect.reshare.indexdata.com/Search/Results?"


def test_isbn():
    params = {"rft.isbn": "978-3-16-148410-0"}
    assert wcd2reshare.query_formatter(params) == "type=ISN&lookfor=978-3-16-148410-0"


def test_title_no_author():
    params = {"rft.title": "salad days"}
    assert wcd2reshare.query_formatter(params) == "type=title&lookfor=salad+days"


def test_title_with_author():
    params = {"rft.title": "salad days", "rft.aulast": "ranch"}
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_btitle_no_author():
    params = {"rft.btitle": "salad days"}
    assert wcd2reshare.query_formatter(params) == "type=title&lookfor=salad+days"


def test_btitle_with_author():
    params = {"rft.btitle": "salad days", "rft.aulast": "ranch"}
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_ctitle_no_author():
    params = {"rft.ctitle": "salad days"}
    assert wcd2reshare.query_formatter(params) == "type=title&lookfor=salad+days"


def test_ctitle_with_author():
    params = {"rft.ctitle": "salad days", "rft.aulast": "ranch"}
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_jtitle_no_author():
    params = {"rft.jtitle": "salad days"}
    assert wcd2reshare.query_formatter(params) == "type=title&lookfor=salad+days"


def test_jtitle_with_author():
    params = {"rft.jtitle": "salad days", "rft.aulast": "ranch"}
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_no_rft_fields_of_interest():
    params = {"rft.popcorn": "sure"}
    assert wcd2reshare.query_formatter(params) == ""


def test_title_priority():
    params = {
        "rft.btitle": "btitle",
        "rft.ctitle": "ctitle",
        "rft.jtitle": "jtitle",
        "rft.aulast": "ranch",
        "rft.title": "title",
    }
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=title&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_btitle_priority():
    params = {
        "rft.ctitle": "ctitle",
        "rft.jtitle": "jtitle",
        "rft.aulast": "ranch",
        "rft.btitle": "btitle",
    }
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=btitle&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_ctitle_priority():
    params = {"rft.jtitle": "jtitle", "rft.aulast": "ranch", "rft.ctitle": "ctitle"}
    assert wcd2reshare.query_formatter(params) == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=ctitle&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )


def test_fields_of_no_interest_ignored():
    params = {"rft.popcorn": "sure", "rft.isbn": "978-3-16-148410-0"}
    assert wcd2reshare.query_formatter(params) == "type=ISN&lookfor=978-3-16-148410-0"


def test_lambda_handler_with_query(baseURL):
    event = {"queryStringParameters": {"rft.isbn": "978-3-16-148410-0"}}
    queryString = "type=ISN&lookfor=978-3-16-148410-0"
    response = wcd2reshare.lambda_handler(event, context={})
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL + queryString


def test_lambda_handler_with_multiple_query(baseURL):
    event = {
        "queryStringParameters": {"rft.title": "salad days", "rft.aulast": "ranch"}
    }
    queryString = (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )
    response = wcd2reshare.lambda_handler(event, context={})
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL + queryString


def test_lambda_handler_without_query(baseURL):
    response = wcd2reshare.lambda_handler(event={}, context={})
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL


def test_lambda_handler_with_garbage_query(baseURL):
    response = wcd2reshare.lambda_handler(
        event={"queryStringParameters": {"door": "knob"}}, context={}
    )
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL


def test_buildSearchString_no_author():
    title = "salad days"
    assert wcd2reshare.buildSearchString(title, aulast=None) == [
        ("type", "title"),
        ("lookfor", title),
    ]


def test_buildSearchString_with_author():
    title = "salad days"
    aulast = "ranch"
    assert wcd2reshare.buildSearchString(title, aulast) == [
        ("join", "AND"),
        ("type0[]", "title"),
        ("lookfor0[]", title),
        ("type0[]", "author"),
        ("lookfor0[]", aulast),
    ]
