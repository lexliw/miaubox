import httpx
import json
import time
from backend.database import get_session, RequestHistory
from backend.env_manager import EnvManager


class RequestRunner:
    def __init__(self, env_manager: EnvManager):
        self.env = env_manager

    def run(
        self,
        method: str,
        url: str,
        headers: dict,
        params: dict,
        body: str,
        body_type: str,
        auth_type: str,
        auth_data: dict,
    ) -> dict:
        url = self.env.resolve(url)
        headers = self.env.resolve_dict(headers)
        params = self.env.resolve_dict(params)
        body = self.env.resolve(body)

        headers = self._apply_auth(headers, auth_type, auth_data)

        kwargs = {"headers": headers, "params": params, "timeout": 30.0}

        if body and method in ("POST", "PUT", "PATCH"):
            if body_type == "json":
                try:
                    kwargs["json"] = json.loads(body)
                except json.JSONDecodeError:
                    kwargs["content"] = body.encode()
            elif body_type == "form":
                kwargs["data"] = dict(
                    item.split("=", 1) for item in body.splitlines() if "=" in item
                )
            else:
                kwargs["content"] = body.encode()

        start = time.time()
        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.request(method, url, **kwargs)
            elapsed = round((time.time() - start) * 1000, 2)

            result = {
                "success": True,
                "status_code": response.status_code,
                "elapsed_ms": elapsed,
                "headers": dict(response.headers),
                "body": self._try_parse_json(response.text),
                "raw": response.text,
                "size": len(response.content),
            }
        except Exception as exc:
            elapsed = round((time.time() - start) * 1000, 2)
            result = {
                "success": False,
                "status_code": 0,
                "elapsed_ms": elapsed,
                "error": str(exc),
                "headers": {},
                "body": None,
                "raw": "",
                "size": 0,
            }

        self._save_history(method, url, result, body)
        return result

    def _apply_auth(self, headers: dict, auth_type: str, auth_data: dict) -> dict:
        if auth_type == "bearer":
            token = self.env.resolve(auth_data.get("token", ""))
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            import base64
            user = self.env.resolve(auth_data.get("username", ""))
            pwd = self.env.resolve(auth_data.get("password", ""))
            encoded = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_type == "api_key":
            key = auth_data.get("header", "X-API-Key")
            val = self.env.resolve(auth_data.get("value", ""))
            headers[key] = val
        return headers

    def _try_parse_json(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            return None

    def _save_history(self, method: str, url: str, result: dict, body: str):
        session = get_session()
        try:
            record = RequestHistory(
                method=method,
                url=url,
                status_code=result["status_code"],
                response_time=result["elapsed_ms"],
                request_data=body,
                response_data=result["raw"][:10000],
            )
            session.add(record)
            session.commit()
        finally:
            session.close()
