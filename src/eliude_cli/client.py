import requests


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None, classroom: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Token {token}"
        if classroom:
            self.session.headers["X-Eliude-Classroom"] = classroom

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
        except requests.exceptions.ConnectionError:
            raise ApiError(f"Could not reach the Eliude server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise ApiError(f"Request to {self.base_url} timed out")

        if response.status_code == 401:
            raise ApiError("Not logged in or token expired. Run `eliude login`.")
        if response.status_code in (400, 403):
            raise ApiError(self._format_validation_errors(response))
        if response.status_code == 404:
            raise ApiError("Not found.")
        response.raise_for_status()
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

    def list_exercises(self) -> list[dict]:
        return self._request("GET", "/api/exercises/").json()

    def get_exercise(self, slug: str) -> dict:
        return self._request("GET", f"/api/exercises/{slug}/").json()

    def submit(self, slug: str, source_code: str) -> dict:
        payload = {"exercise_slug": slug, "source_code": source_code}
        return self._request("POST", "/api/submissions/", json=payload).json()

    def get_submission(self, submission_id: int) -> dict:
        return self._request("GET", f"/api/submissions/{submission_id}/").json()

    def list_classrooms(self) -> list[dict]:
        return self._request("GET", "/api/classrooms/").json()
