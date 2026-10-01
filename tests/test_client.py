import pytest
import requests

from eliude_cli.client import ApiClient, ApiError

BASE_URL = "http://eliude.test"


def make_response(status_code, method="GET", url=BASE_URL + "/api/x/", history=None, body=b"{}"):
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    response._content = body
    response.request = requests.Request(method, url).prepare()
    response.history = history or []
    return response


def stub_request(monkeypatch, client, response=None, exc=None):
    def fake_request(method, url, **kwargs):
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(client.session, "request", fake_request)


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
def test_server_errors_become_a_friendly_api_error(cli_config, monkeypatch, status_code):
    client = ApiClient(BASE_URL)
    stub_request(monkeypatch, client, make_response(status_code))
    with pytest.raises(ApiError, match=f"ran into an error \\(HTTP {status_code}\\)"):
        client._request("GET", "/api/x/")


def test_rate_limit_becomes_a_friendly_api_error(cli_config, monkeypatch):
    client = ApiClient(BASE_URL)
    stub_request(monkeypatch, client, make_response(429))
    with pytest.raises(ApiError, match="Too many requests"):
        client._request("POST", "/api/x/")


def test_other_client_errors_become_an_api_error(cli_config, monkeypatch):
    client = ApiClient(BASE_URL)
    stub_request(monkeypatch, client, make_response(418))
    with pytest.raises(ApiError, match="HTTP 418"):
        client._request("GET", "/api/x/")


def test_redirect_that_turned_post_into_get_points_at_set_url(cli_config, monkeypatch):
    client = ApiClient("http://eliude.test/eliude")
    final_url = "https://eliude.test/eliude/api/auth/signup/"
    redirect = make_response(301, method="POST", url="http://eliude.test/eliude/api/auth/signup/")
    stub_request(monkeypatch, client, make_response(405, method="GET", url=final_url, history=[redirect]))
    with pytest.raises(ApiError, match="eliude config set-url https://eliude.test/eliude$"):
        client._request("POST", "/api/auth/signup/")


def test_unexpected_network_failure_becomes_an_api_error(cli_config, monkeypatch):
    client = ApiClient(BASE_URL)
    stub_request(monkeypatch, client, exc=requests.exceptions.TooManyRedirects())
    with pytest.raises(ApiError, match="Could not complete the request"):
        client._request("GET", "/api/x/")


def test_errors_follow_the_configured_language(cli_config, monkeypatch):
    cli_config.set_language("pt-BR")
    client = ApiClient(BASE_URL)
    stub_request(monkeypatch, client, make_response(500))
    with pytest.raises(ApiError, match="O servidor Eliude encontrou um erro \\(HTTP 500\\)"):
        client._request("GET", "/api/x/")


def test_success_is_returned_untouched(cli_config, monkeypatch):
    client = ApiClient(BASE_URL)
    response = make_response(201, method="POST")
    stub_request(monkeypatch, client, response)
    assert client._request("POST", "/api/x/") is response
