import requests

from .messages import t


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(
        self, base_url: str, token: str | None = None, classroom: str | None = None, practice: str | None = None
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Token {token}"
        if classroom:
            self.session.headers["X-Eliude-Classroom"] = classroom
        if practice:
            self.session.headers["X-Eliude-Practice"] = practice

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
        except requests.exceptions.ConnectionError:
            raise ApiError(t("api.unreachable", url=self.base_url))
        except requests.exceptions.Timeout:
            raise ApiError(t("api.timeout", url=self.base_url))
        except requests.exceptions.RequestException:
            raise ApiError(t("api.request_failed", url=self.base_url))

        # A redirect (e.g. http -> https) silently turns a POST into a GET,
        # which then fails with a confusing 405 — point at the real fix.
        if response.history and response.request.method != method.upper():
            new_base = response.url[: -len(path)] if response.url.endswith(path) else response.url
            raise ApiError(t("api.redirected", url=new_base.rstrip("/")))

        if response.status_code == 401:
            raise ApiError(t("api.not_logged_in"))
        if response.status_code in (400, 403):
            raise ApiError(self._format_validation_errors(response))
        if response.status_code == 404:
            raise ApiError(t("api.not_found"))
        if response.status_code == 429:
            raise ApiError(t("api.rate_limited"))
        if response.status_code >= 500:
            raise ApiError(t("api.server_error", status=response.status_code))
        if response.status_code >= 400:
            raise ApiError(t("api.unexpected_status", status=response.status_code))
        return response

    @staticmethod
    def _format_validation_errors(response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text
        if isinstance(body, dict):
            if set(body.keys()) == {"detail"}:
                return str(body["detail"])
            parts = [f"{field}: {', '.join(msgs) if isinstance(msgs, list) else msgs}" for field, msgs in body.items()]
            return "; ".join(parts)
        return str(body)

    def login(self, username: str, password: str) -> str:
        response = self._request("POST", "/api/auth/login/", data={"username": username, "password": password})
        return response.json()["token"]

    def signup(self, name: str, email: str, password: str, password_confirm: str, classroom_code: str) -> dict:
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "password_confirm": password_confirm,
            "classroom_code": classroom_code,
        }
        return self._request("POST", "/api/auth/signup/", json=payload).json()

    def logout(self) -> None:
        self._request("POST", "/api/auth/logout/")

    def change_password(self, current_password: str, new_password: str, new_password_confirm: str) -> None:
        payload = {
            "current_password": current_password,
            "new_password": new_password,
            "new_password_confirm": new_password_confirm,
        }
        self._request("POST", "/api/auth/change-password/", json=payload)

    def list_questions(self, tag: str | None = None) -> list[dict]:
        params = {"tag": tag} if tag else None
        return self._request("GET", "/api/practice-questions/", params=params).json()

    def get_question(self, slug: str) -> dict:
        return self._request("GET", f"/api/practice-questions/{slug}/").json()

    def submit(self, slug: str, source_code: str) -> dict:
        payload = {"source_code": source_code}
        return self._request("POST", f"/api/practice-questions/{slug}/submit/", json=payload).json()

    def get_submission(self, submission_id: int) -> dict:
        return self._request("GET", f"/api/submissions/{submission_id}/").json()

    def get_latest_submission(self, slug: str) -> dict:
        return self._request("GET", f"/api/practice-questions/{slug}/latest/").json()

    def list_classrooms(self) -> list[dict]:
        return self._request("GET", "/api/classrooms/").json()

    def list_practices(self) -> list[dict]:
        return self._request("GET", "/api/practices/").json()

    def start_practice(self, slug: str) -> dict:
        return self._request("POST", f"/api/practices/{slug}/start/").json()

    def get_latest_release(self) -> dict:
        return self._request("GET", "/api/cli/latest/").json()

    def get_health(self) -> dict:
        return self._request("GET", "/api/health/").json()
