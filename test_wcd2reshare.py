import os
from importlib import reload
from unittest.mock import MagicMock

import pytest
import requests_mock

import wcd2reshare


@pytest.fixture(autouse=True)
def test_env():
    os.environ = {
        "WORKSPACE": "test",
    }
    return


@pytest.fixture
def baseURL():
    return "https://borrowdirect.reshare.indexdata.com/Search/Results?"


@pytest.fixture
def mocked_searchHasResults(*args, **kwargs):
    if args[0].get("oclc"):
        return False

    if args[0].get("isbn"):
        return False

    if args[0].get("title"):
        return True


def test_configures_sentry_if_dsn_present(caplog, monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    reload(wcd2reshare)
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test"
        in caplog.text
    )


def test_doesnt_configure_sentry_if_dsn_not_present(caplog, monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    reload(wcd2reshare)
    assert "Sentry DSN found" not in caplog.text


def test_query_formatter():
    params = {
        "rft.isbn": "978-3-16-148410-0",
        "rft.title": "salad days",
        "rft_id": "info%3Aoclcnum%2F12345678",
    }
    SearchStrings = wcd2reshare.query_formatter(params)
    assert SearchStrings["oclc"] == "type=oclc_num&lookfor=12345678"
    assert SearchStrings["isbn"] == "type=ISN&lookfor=978-3-16-148410-0"
    assert SearchStrings["title"] == "type=title&lookfor=salad+days"


def test_query_formatter_title_with_author():
    params = {"rft.title": "salad days", "rft.aulast": "ranch"}
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_no_rft_fields_of_interest():
    params = {"rft.popcorn": "sure"}
    assert wcd2reshare.query_formatter(params) == {}


def test_query_formatter_title_priority():
    params = {
        "rft.btitle": "b title",
        "rft.ctitle": "c title",
        "rft.jtitle": "j title",
        "rft.aulast": "ranch",
        "rft.title": "salad days",
    }
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_btitle_priority():
    params = {
        "rft.ctitle": "c title",
        "rft.jtitle": "j title",
        "rft.aulast": "ranch",
        "rft.btitle": "b title",
    }
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=b+title&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_ctitle_priority():
    params = {"rft.jtitle": "j title", "rft.aulast": "ranch", "rft.ctitle": "c title"}
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=c+title&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_fields_of_no_interest_ignored():
    params = {"rft.popcorn": "sure", "rft.isbn": "978-3-16-148410-0"}
    assert wcd2reshare.query_formatter(params)["isbn"] == (
        "type=ISN&lookfor=978-3-16-148410-0"
    )


def test_searchHasResults_is_true_when_results_are_returned():
    searchString = "successful search string"
    with requests_mock.Mocker() as m:
        m.request(requests_mock.ANY, requests_mock.ANY, json={"resultCount": 1})
        assert wcd2reshare.searchHasResults(searchString) is True


def test_searchHasResults_is_false_when_results_are_not_returned():
    searchString = "failing search string"
    with requests_mock.Mocker() as m:
        m.request(requests_mock.ANY, requests_mock.ANY, json={"resultCount": 0})
        assert wcd2reshare.searchHasResults(searchString) is False


def test_buildTitleSearchString_no_author():
    title = "salad days"
    assert wcd2reshare.buildTitleSearchString(title, aulast=None) == [
        ("type", "title"),
        ("lookfor", title),
    ]


def test_selectSearchStrategy_no_success():
    searchStrings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    wcd2reshare.searchHasResults = MagicMock(side_effect=[False, False, False])
    selectedStrategy = wcd2reshare.selectSearchStrategy(searchStrings)
    assert wcd2reshare.searchHasResults.call_count == 3
    assert selectedStrategy == ""


def test_selectSearchStrategy_oclc_success():
    searchStrings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    wcd2reshare.searchHasResults = MagicMock(side_effect=[True])
    selectedStrategy = wcd2reshare.selectSearchStrategy(searchStrings)
    assert wcd2reshare.searchHasResults.call_count == 1
    assert selectedStrategy == searchStrings["oclc"]


def test_selectSearchStrategy_isbn_success():
    searchStrings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    wcd2reshare.searchHasResults = MagicMock(side_effect=[False, True])
    selectedStrategy = wcd2reshare.selectSearchStrategy(searchStrings)
    assert wcd2reshare.searchHasResults.call_count == 2
    assert selectedStrategy == searchStrings["isbn"]


def test_selectSearchStrategy_title_success():
    searchStrings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    wcd2reshare.searchHasResults = MagicMock(side_effect=[False, False, True])
    selectedStrategy = wcd2reshare.selectSearchStrategy(searchStrings)
    assert wcd2reshare.searchHasResults.call_count == 3
    assert selectedStrategy == searchStrings["title"]


def test_buildTitleSearchString_with_author():
    title = "salad days"
    aulast = "ranch"
    assert wcd2reshare.buildTitleSearchString(title, aulast) == [
        ("join", "AND"),
        ("type0[]", "title"),
        ("lookfor0[]", title),
        ("type0[]", "author"),
        ("lookfor0[]", aulast),
    ]


def test_lambda_handler_workspace_missing(caplog, monkeypatch):
    monkeypatch.delenv("WORKSPACE")
    reload(wcd2reshare)
    with pytest.raises(ValueError):
        wcd2reshare.lambda_handler({}, {})


def test_lambda_handler_workspace_found(caplog):
    reload(wcd2reshare)
    wcd2reshare.lambda_handler({}, {})
    assert "Required WORKSPACE env is None" not in caplog.text


def test_lambda_handler_with_query(baseURL):
    event = {"queryStringParameters": {"rft.isbn": "978-3-16-148410-0"}}
    queryString = "type=ISN&lookfor=978-3-16-148410-0"
    wcd2reshare.selectSearchStrategy = MagicMock(return_value=queryString)
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
    wcd2reshare.selectSearchStrategy = MagicMock(return_value=queryString)
    response = wcd2reshare.lambda_handler(event, context={})
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL + queryString


def test_lambda_handler_without_query(baseURL):
    response = wcd2reshare.lambda_handler(event={}, context={})
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL


def test_lambda_handler_with_garbage_query(baseURL):
    wcd2reshare.selectSearchStrategy = MagicMock(return_value="")
    response = wcd2reshare.lambda_handler(
        event={"queryStringParameters": {"door": "knob"}}, context={}
    )
    assert response["statusCode"] == 307
    assert response["headers"]["Location"] == baseURL
