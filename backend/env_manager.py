import re
import json
from backend.database import get_session, Environment, EnvVariable


class EnvManager:
    """Gerencia variáveis de ambiente e substituição {{VAR_NAME}}."""

    def __init__(self):
        self._cache: dict[str, str] = {}
        self._active_env_id: int | None = None
        self.reload()

    def reload(self):
        """Recarrega variáveis do ambiente ativo."""
        self._cache = {}
        session = get_session()
        try:
            env = session.query(Environment).filter_by(is_active=True).first()
            if env:
                self._active_env_id = env.id
                for var in env.variables:
                    self._cache[var.key] = var.value
        finally:
            session.close()

    def resolve(self, text: str) -> str:
        """Substitui {{VAR_NAME}} pelo valor correspondente."""
        if not text:
            return text

        def replacer(match):
            key = match.group(1).strip()
            return self._cache.get(key, match.group(0))

        return re.sub(r"\{\{([^}]+)\}\}", replacer, text)

    def resolve_dict(self, data: dict) -> dict:
        """Resolve variáveis em todos os valores de um dict."""
        return {k: self.resolve(v) for k, v in data.items()}

    def get_active_env_name(self) -> str:
        session = get_session()
        try:
            env = session.query(Environment).filter_by(is_active=True).first()
            return env.name if env else "Nenhum"
        finally:
            session.close()

    # ── CRUD ──────────────────────────────────────────────

    def list_environments(self) -> list[dict]:
        session = get_session()
        try:
            envs = session.query(Environment).all()
            return [
                {"id": e.id, "name": e.name, "is_active": e.is_active}
                for e in envs
            ]
        finally:
            session.close()

    def create_environment(self, name: str) -> int:
        session = get_session()
        try:
            env = Environment(name=name)
            session.add(env)
            session.commit()
            session.refresh(env)
            return env.id
        finally:
            session.close()

    def delete_environment(self, env_id: int):
        session = get_session()
        try:
            env = session.query(Environment).filter_by(id=env_id).first()
            if env:
                session.delete(env)
                session.commit()
        finally:
            session.close()

    def set_active_environment(self, env_id: int):
        session = get_session()
        try:
            session.query(Environment).update({"is_active": False})
            env = session.query(Environment).filter_by(id=env_id).first()
            if env:
                env.is_active = True
            session.commit()
        finally:
            session.close()
        self.reload()

    def get_variables(self, env_id: int) -> list[dict]:
        session = get_session()
        try:
            vars_ = session.query(EnvVariable).filter_by(environment_id=env_id).all()
            return [
                {"id": v.id, "key": v.key, "value": v.value, "is_secret": v.is_secret}
                for v in vars_
            ]
        finally:
            session.close()

    def upsert_variable(self, env_id: int, key: str, value: str, is_secret: bool = False):
        session = get_session()
        try:
            var = session.query(EnvVariable).filter_by(environment_id=env_id, key=key).first()
            if var:
                var.value = value
                var.is_secret = is_secret
            else:
                var = EnvVariable(environment_id=env_id, key=key, value=value, is_secret=is_secret)
                session.add(var)
            session.commit()
        finally:
            session.close()
        self.reload()

    def delete_variable(self, var_id: int):
        session = get_session()
        try:
            var = session.query(EnvVariable).filter_by(id=var_id).first()
            if var:
                session.delete(var)
                session.commit()
        finally:
            session.close()
        self.reload()

    def export_environment(self, env_id: int) -> str:
        session = get_session()
        try:
            env = session.query(Environment).filter_by(id=env_id).first()
            if not env:
                return "{}"
            data = {
                "name": env.name,
                "variables": [
                    {"key": v.key, "value": v.value, "is_secret": v.is_secret}
                    for v in env.variables
                ],
            }
            return json.dumps(data, indent=2, ensure_ascii=False)
        finally:
            session.close()

    def import_environment(self, json_str: str):
        data = json.loads(json_str)
        env_id = self.create_environment(data["name"])
        for var in data.get("variables", []):
            self.upsert_variable(env_id, var["key"], var["value"], var.get("is_secret", False))
