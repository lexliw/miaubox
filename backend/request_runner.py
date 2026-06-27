import httpx
import json
import time
import traceback
from backend.database import get_session, RequestHistory
from backend.env_manager import EnvManager


class RequestContext:
    """Objeto 'request' disponível nos scripts."""
    def __init__(self, method, url, headers, params, body):
        self.method = method
        self.url = url
        self.headers = headers
        self.params = params
        self.body = body


class ResponseContext:
    """Objeto 'response' disponível nos scripts pós-requisição."""
    def __init__(self, status_code, headers, body_json, raw):
        self.status_code = status_code
        self.headers = headers
        self._json = body_json
        self.raw = raw

    def json(self):
        return self._json


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
        pre_script: str = "",
        pos_script: str = "",
    ) -> dict:
        logs = []

        # ── Resolve variáveis de ambiente ─────────────────
        url = self.env.resolve(url)
        headers = self.env.resolve_dict(headers)
        params = self.env.resolve_dict(params)
        body = self.env.resolve(body)

        # ── Autenticação ──────────────────────────────────
        headers = self._apply_auth(headers, auth_type, auth_data)

        # ── Objeto request para o script ──────────────────
        req_ctx = RequestContext(method, url, headers, params, body)
        env_proxy = _EnvProxy(self.env)

        # ── Executa pré-script ────────────────────────────
        if pre_script and pre_script.strip():
            log, error = self._run_script(
                pre_script,
                sandbox={"request": req_ctx, "env": env_proxy},
                label="pré-requisição"
            )
            logs.append(log)
            if error:
                return {
                    "success": False,
                    "status_code": 0,
                    "elapsed_ms": 0,
                    "error": f"Erro no script pré-requisição:\n{error}",
                    "headers": {}, "body": None, "raw": "", "size": 0,
                    "script_log": "\n".join(logs),
                }

            # ✅ Atualiza TODOS os campos que o script pode ter modificado
            url     = req_ctx.url
            headers = req_ctx.headers
            params  = req_ctx.params
            body    = req_ctx.body  # ← correção principal

        # ── Monta kwargs do httpx ─────────────────────────
        # ✅ Usa o body já atualizado pelo pré-script (se houver)
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

        # ── Executa requisição ────────────────────────────
        start = time.time()
        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.request(method, url, **kwargs)
            elapsed = round((time.time() - start) * 1000, 2)

            body_json = self._try_parse_json(response.text)

            result = {
                "success": True,
                "status_code": response.status_code,
                "elapsed_ms": elapsed,
                "headers": dict(response.headers),
                "body": body_json,
                "raw": response.text,
                "size": len(response.content),
                "script_log": "\n".join(logs),  # <- pré-script já aparece aqui
            }

            # ── Executa pós-script ────────────────────────
            if pos_script and pos_script.strip():
                res_ctx = ResponseContext(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body_json=body_json,
                    raw=response.text,
                )
                log, error = self._run_script(
                    pos_script,
                    sandbox={
                        "request": req_ctx,
                        "response": res_ctx,
                        "env": env_proxy,
                    },
                    label="pós-requisição"
                )
                logs.append(log)
                if error:
                    result["script_log"] = "\n".join(logs) + f"\n❌ {error}"
                else:
                    result["script_log"] = "\n".join(logs)

        except Exception as exc:
            elapsed = round((time.time() - start) * 1000, 2)
            result = {
                "success": False,
                "status_code": 0,
                "elapsed_ms": elapsed,
                "error": str(exc),
                "headers": {}, "body": None, "raw": "", "size": 0,
                "script_log": "\n".join(logs),
            }

        self._save_history(method, url, result, body)
        return result

    def _run_script(self, code: str, sandbox: dict, label: str) -> tuple[str, str]:
        import io
        import sys

        output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output

        error_msg = ""
        try:
            exec(compile(code, f"<{label}>", "exec"), sandbox)
        except Exception:
            error_msg = traceback.format_exc()
        finally:
            sys.stdout = old_stdout

        printed = output.getvalue()
        log_lines = [f"── {label} ──"]
        if printed:
            log_lines.append(printed.strip())
        if not error_msg:
            log_lines.append("✅ Executado com sucesso")
        return "\n".join(log_lines), error_msg

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


class _EnvProxy:
    """
    Proxy que permite scripts lerem e escreverem variáveis
    de ambiente via env["KEY"] = "value".
    """
    def __init__(self, env_manager: EnvManager):
        self._env = env_manager

    def __getitem__(self, key: str) -> str:
        return self._env._cache.get(key, "")

    def __setitem__(self, key: str, value: str):
        env_id = self._env._active_env_id
        if env_id:
            self._env.upsert_variable(env_id, key, str(value))

    def __repr__(self):
        return str(self._env._cache)