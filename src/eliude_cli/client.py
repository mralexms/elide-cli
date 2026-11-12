import requests

from .messages import t


class ApiError(Exception):
    def __init__(self, message: str, status: int | None = None, code: str | None = None, data: dict | None = None):
        super().__init__(message)
        self.status = status
        # The backend's error code, when it sends one (e.g. "practice_finished").
        self.code = code
        # The rest of the error body, e.g. the current version in a 409.
        self.data = data or {}


# Error codes the backend sends in the body ({"detail": ..., "code": ...})
# that get a message of their own, in the CLI's language.
_CODE_MESSAGES = {"practice_finished": "api.practice_finished"}


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
            code = self._error_code(response)
            if code in _CODE_MESSAGES:
                raise ApiError(t(_CODE_MESSAGES[code]), status=response.status_code, code=code)
            raise ApiError(self._format_validation_errors(response), status=response.status_code, code=code)
        if response.status_code == 404:
            raise ApiError(t("api.not_found"), status=404)
        if response.status_code == 409:
            body = self._json_dict(response)
            raise ApiError(str(body.get("detail", "")), status=409, code=self._error_code(response), data=body)
        if response.status_code == 429:
            raise ApiError(t("api.rate_limited"))
        if response.status_code >= 500:
            raise ApiError(t("api.server_error", status=response.status_code), status=response.status_code)
        if response.status_code >= 400:
            raise ApiError(t("api.unexpected_status", status=response.status_code))
        return response

    @staticmethod
    def _json_dict(response) -> dict:
        try:
            body = response.json()
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}

    @staticmethod
    def _error_code(response) -> str | None:
        try:
            body = response.json()
        except ValueError:
            return None
        code = body.get("code") if isinstance(body, dict) else None
        return code if isinstance(code, str) else None

    @staticmethod
    def _format_validation_errors(response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text
        if isinstance(body, dict):
            if set(body.keys()) in ({"detail"}, {"detail", "code"}):
                return str(body["detail"])
            parts = [f"{field}: {', '.join(msgs) if isinstance(msgs, list) else msgs}" for field, msgs in body.items()]
            return "; ".join(parts)
        return str(body)

    def request_login_code(self, login: str) -> dict:
        """Asks the server to email a login code to the account `login` (its
        email or username) identifies. The answer is the same whether or
        not the account exists: {"detail", "minutes"}."""
        return self._request("POST", "/api/auth/code/", data={"login": login}).json()

    def verify_login_code(self, login: str, code: str) -> dict:
        """Trades a login code for {"token", "username"}. A wrong or expired
        code is a 400."""
        return self._request("POST", "/api/auth/code/verify/", data={"login": login, "code": code}).json()

    def logout(self) -> None:
        self._request("POST", "/api/auth/logout/")

    def list_questions(self, tag: str | None = None) -> list[dict]:
        params = {"tag": tag} if tag else None
        return self._request("GET", "/api/practice-questions/", params=params).json()

    def get_question(self, slug: str) -> dict:
        return self._request("GET", f"/api/practice-questions/{slug}/").json()

    def submit(self, slug: str, files: dict[str, str]) -> dict:
        payload = {"files": files}
        return self._request("POST", f"/api/practice-questions/{slug}/submit/", json=payload).json()

    def get_submission(self, submission_id: int) -> dict:
        return self._request("GET", f"/api/submissions/{submission_id}/").json()

    def get_latest_submission(self, slug: str) -> dict:
        return self._request("GET", f"/api/practice-questions/{slug}/latest/").json()

    def get_draft(self, slug: str) -> dict | None:
        """The code saved without grading for a question, or None if there's
        none: {"version", "updated_at", "files": [{"path", "content"}]}."""
        try:
            return self._request("GET", f"/api/practice-questions/{slug}/draft/").json()
        except ApiError as e:
            if e.status == 404:
                return None
            raise

    def save_draft(self, slug: str, files: dict[str, str], base_version: int | None = None) -> dict:
        """Saves the code without grading. With base_version (the version
        that was opened, 0 for none), the server refuses with a 409
        (code "draft_conflict") if someone saved since."""
        payload: dict = {"files": files}
        if base_version is not None:
            payload["base_version"] = base_version
        return self._request("PUT", f"/api/practice-questions/{slug}/draft/", json=payload).json()

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
