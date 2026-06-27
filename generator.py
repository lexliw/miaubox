# %%!/usr/bin/env python3
"""
MiauBox Project Generator
Cria toda a estrutura de diretórios e arquivos do projeto MiauBox.
Execute: python generate_miaubox.py
"""

import os

# ── Conteúdo de cada arquivo ──────────────────────────────────────────────────

FILES = {}

# ── requirements.txt ─────────────────────────────────────────────────────────
FILES["requirements.txt"] = """\
customtkinter==5.2.2
httpx==0.27.0
sqlalchemy==2.0.30
Pillow==10.3.0
pygments==2.18.0
"""

# ── backend/__init__.py ───────────────────────────────────────────────────────
FILES["backend/__init__.py"] = ""

# ── ui/__init__.py ────────────────────────────────────────────────────────────
FILES["ui/__init__.py"] = ""

# ── assets/.gitkeep ──────────────────────────────────────────────────────────
FILES["assets/.gitkeep"] = ""

# ── backend/database.py ───────────────────────────────────────────────────────
FILES["backend/database.py"] = '''\
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///miaubox.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    requests = relationship("SavedRequest", back_populates="collection", cascade="all, delete-orphan")


class SavedRequest(Base):
    __tablename__ = "saved_requests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    method = Column(String, default="GET")
    url = Column(Text, default="")
    headers = Column(Text, default="{}")
    params = Column(Text, default="{}")
    body = Column(Text, default="")
    body_type = Column(String, default="json")
    auth_type = Column(String, default="none")
    auth_data = Column(Text, default="{}")
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    collection = relationship("Collection", back_populates="requests")
    created_at = Column(DateTime, default=datetime.utcnow)


class RequestHistory(Base):
    __tablename__ = "request_history"
    id = Column(Integer, primary_key=True, index=True)
    method = Column(String)
    url = Column(Text)
    status_code = Column(Integer)
    response_time = Column(Float)
    request_data = Column(Text)
    response_data = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)


class Environment(Base):
    __tablename__ = "environments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=False)
    variables = relationship("EnvVariable", back_populates="environment", cascade="all, delete-orphan")


class EnvVariable(Base):
    __tablename__ = "env_variables"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    value = Column(Text, default="")
    is_secret = Column(Boolean, default=False)
    environment_id = Column(Integer, ForeignKey("environments.id"))
    environment = relationship("Environment", back_populates="variables")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
'''

# ── backend/env_manager.py ────────────────────────────────────────────────────
FILES["backend/env_manager.py"] = '''\
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

        return re.sub(r"\\{\\{([^}]+)\\}\\}", replacer, text)

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
'''

# ── backend/request_runner.py ─────────────────────────────────────────────────
FILES["backend/request_runner.py"] = '''\
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
'''

# ── ui/styles.py ──────────────────────────────────────────────────────────────
FILES["ui/styles.py"] = '''\
DARK = {
    "bg": "#1a1a2e",
    "surface": "#16213e",
    "surface2": "#0f3460",
    "accent": "#e94560",
    "accent2": "#533483",
    "text": "#eaeaea",
    "text_dim": "#888aaa",
    "success": "#4ade80",
    "warning": "#facc15",
    "error": "#f87171",
    "border": "#2a2a4a",
}

LIGHT = {
    "bg": "#f5f5f5",
    "surface": "#ffffff",
    "surface2": "#e8e8f0",
    "accent": "#e94560",
    "accent2": "#533483",
    "text": "#1a1a2e",
    "text_dim": "#555577",
    "success": "#16a34a",
    "warning": "#ca8a04",
    "error": "#dc2626",
    "border": "#d1d1e0",
}

METHOD_COLORS = {
    "GET": "#4ade80",
    "POST": "#facc15",
    "PUT": "#60a5fa",
    "PATCH": "#a78bfa",
    "DELETE": "#f87171",
}

STATUS_COLORS = {
    "2": "#4ade80",
    "3": "#60a5fa",
    "4": "#facc15",
    "5": "#f87171",
}


def status_color(code: int) -> str:
    key = str(code)[0] if code else "5"
    return STATUS_COLORS.get(key, "#f87171")
'''

# ── ui/sidebar.py ─────────────────────────────────────────────────────────────
FILES["ui/sidebar.py"] = '''\
import customtkinter as ctk
import json
from backend.database import get_session, Collection, SavedRequest
from ui.styles import DARK, METHOD_COLORS


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_load_request, theme=DARK, **kwargs):
        super().__init__(master, fg_color=theme["surface"], width=260, **kwargs)
        self.theme = theme
        self.on_load_request = on_load_request
        self._col_expanded: dict[int, bool] = {}
        self._build()
        self.refresh()

    def _build(self):
        t = self.theme

        header = ctk.CTkFrame(self, fg_color=self.theme["surface2"], corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            header, text="🐱 MiauBox", font=("JetBrains Mono", 18, "bold"),
            text_color=t["accent"]
        ).pack(pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ctk.CTkEntry(
            self, placeholder_text="🔍 Buscar...", textvariable=self.search_var,
            fg_color=t["surface2"], border_color=t["border"], text_color=t["text"]
        ).pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkButton(
            self, text="+ Nova Coleção", fg_color=t["accent2"],
            hover_color=t["accent"], text_color="white",
            command=self._new_collection
        ).pack(fill="x", padx=10, pady=4)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=self.theme["surface"], label_text=""
        )
        self.scroll.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkButton(
            self, text="🕑 Histórico", fg_color=t["surface2"],
            hover_color=t["border"], text_color=t["text_dim"],
            command=self._show_history
        ).pack(fill="x", padx=10, pady=(4, 8))

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        query = self.search_var.get().lower()
        session = get_session()
        try:
            collections = session.query(Collection).all()
            for col in collections:
                self._render_collection(col, query)
        finally:
            session.close()

    def _render_collection(self, col, query: str):
        t = self.theme

        col_frame = ctk.CTkFrame(self.scroll, fg_color=t["surface2"], corner_radius=6)
        col_frame.pack(fill="x", padx=4, pady=2)

        row = ctk.CTkFrame(col_frame, fg_color="transparent")
        row.pack(fill="x")

        is_open = self._col_expanded.get(col.id, True)

        ctk.CTkButton(
            row, text=f"{\\'▾\\' if is_open else \\'▸\\'} 📁 {col.name}",
            fg_color="transparent", hover_color=t["border"],
            text_color=t["text"], anchor="w", font=("JetBrains Mono", 12, "bold"),
            command=lambda cid=col.id: self._toggle_collection(cid)
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            row, text="✕", width=24, fg_color="transparent",
            hover_color=t["error"], text_color=t["text_dim"],
            command=lambda cid=col.id: self._delete_collection(cid)
        ).pack(side="right", padx=2)

        if is_open:
            for req in col.requests:
                if query and query not in req.name.lower() and query not in req.url.lower():
                    continue
                self._render_request_item(col_frame, req)

        ctk.CTkButton(
            col_frame, text="+ request", fg_color="transparent",
            hover_color=t["border"], text_color=t["text_dim"],
            font=("JetBrains Mono", 10), anchor="w",
            command=lambda cid=col.id: self._new_request(cid)
        ).pack(fill="x", padx=8, pady=2)

    def _render_request_item(self, parent, req):
        t = self.theme
        method_color = METHOD_COLORS.get(req.method, t["text_dim"])

        item = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        item.pack(fill="x", padx=8, pady=1)

        ctk.CTkLabel(
            item, text=req.method, font=("JetBrains Mono", 9, "bold"),
            text_color=method_color, width=40
        ).pack(side="left")

        ctk.CTkLabel(
            item, text=req.name, font=("JetBrains Mono", 11),
            text_color=t["text"], anchor="w"
        ).pack(side="left", fill="x", expand=True)

        item.bind("<Button-1>", lambda _e, r=req: self._load(r))
        for child in item.winfo_children():
            child.bind("<Button-1>", lambda _e, r=req: self._load(r))

    def _load(self, req):
        data = {
            "id": req.id,
            "name": req.name,
            "method": req.method,
            "url": req.url,
            "headers": req.headers,
            "params": req.params,
            "body": req.body,
            "body_type": req.body_type,
            "auth_type": req.auth_type,
            "auth_data": req.auth_data,
        }
        self.on_load_request(data)

    def _toggle_collection(self, col_id: int):
        self._col_expanded[col_id] = not self._col_expanded.get(col_id, True)
        self.refresh()

    def _new_collection(self):
        dialog = ctk.CTkInputDialog(text="Nome da coleção:", title="Nova Coleção")
        name = dialog.get_input()
        if name:
            session = get_session()
            try:
                session.add(Collection(name=name))
                session.commit()
            finally:
                session.close()
            self.refresh()

    def _new_request(self, col_id: int):
        dialog = ctk.CTkInputDialog(text="Nome da requisição:", title="Nova Requisição")
        name = dialog.get_input()
        if name:
            session = get_session()
            try:
                session.add(SavedRequest(name=name, collection_id=col_id))
                session.commit()
            finally:
                session.close()
            self.refresh()

    def _delete_collection(self, col_id: int):
        session = get_session()
        try:
            col = session.query(Collection).filter_by(id=col_id).first()
            if col:
                session.delete(col)
                session.commit()
        finally:
            session.close()
        self.refresh()

    def _show_history(self):
        from ui.history_window import HistoryWindow
        HistoryWindow(self, self.theme, self.on_load_request)
'''

# ── ui/request_panel.py ───────────────────────────────────────────────────────
FILES["ui/request_panel.py"] = '''\
import customtkinter as ctk
import json
from ui.styles import DARK, METHOD_COLORS


class RequestPanel(ctk.CTkFrame):
    def __init__(self, master, on_send, on_save, env_manager, theme=DARK, **kwargs):
        super().__init__(master, fg_color=theme["bg"], **kwargs)
        self.theme = theme
        self.on_send = on_send
        self.on_save = on_save
        self.env = env_manager
        self._current_id = None
        self._build()

    def _build(self):
        t = self.theme

        top = ctk.CTkFrame(self, fg_color=t["surface"], corner_radius=8)
        top.pack(fill="x", padx=12, pady=(12, 4))

        self.method_var = ctk.StringVar(value="GET")
        ctk.CTkOptionMenu(
            top, values=["GET", "POST", "PUT", "PATCH", "DELETE"],
            variable=self.method_var, width=100,
            fg_color=t["surface2"], button_color=t["accent2"],
            dropdown_fg_color=t["surface"], text_color=t["text"],
            command=self._update_method_color
        ).pack(side="left", padx=(8, 4), pady=8)

        self.url_var = ctk.StringVar()
        ctk.CTkEntry(
            top, textvariable=self.url_var, placeholder_text="https://api.exemplo.com/endpoint",
            fg_color=t["surface2"], border_color=t["border"],
            text_color=t["text"], font=("JetBrains Mono", 13)
        ).pack(side="left", fill="x", expand=True, padx=4, pady=8)

        ctk.CTkButton(
            top, text="▶  Enviar", fg_color=t["accent"],
            hover_color=t["accent2"], text_color="white",
            font=("JetBrains Mono", 13, "bold"), width=110,
            command=self._send
        ).pack(side="left", padx=(4, 4), pady=8)

        ctk.CTkButton(
            top, text="💾 Salvar", fg_color=t["surface2"],
            hover_color=t["border"], text_color=t["text"],
            width=90, command=self._save
        ).pack(side="left", padx=(0, 8), pady=8)

        name_row = ctk.CTkFrame(self, fg_color="transparent")
        name_row.pack(fill="x", padx=12, pady=(0, 4))

        self.name_var = ctk.StringVar(value="Nova Requisição")
        ctk.CTkEntry(
            name_row, textvariable=self.name_var,
            fg_color="transparent", border_width=0,
            text_color=t["text_dim"], font=("JetBrains Mono", 11)
        ).pack(side="left")

        self.tab_view = ctk.CTkTabview(
            self, fg_color=t["surface"],
            segmented_button_fg_color=t["surface2"],
            segmented_button_selected_color=t["accent"],
            segmented_button_selected_hover_color=t["accent2"],
            segmented_button_unselected_color=t["surface2"],
            text_color=t["text"]
        )
        self.tab_view.pack(fill="both", expand=True, padx=12, pady=4)

        for tab in ["Headers", "Params", "Body", "Auth"]:
            self.tab_view.add(tab)

        self._build_headers_tab()
        self._build_params_tab()
        self._build_body_tab()
        self._build_auth_tab()

    def _build_headers_tab(self):
        frame = self.tab_view.tab("Headers")
        t = self.theme
        self._headers_rows: list[tuple] = []
        self._headers_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._headers_scroll.pack(fill="both", expand=True)
        ctk.CTkButton(
            frame, text="+ Header", fg_color=t["surface2"],
            hover_color=t["border"], text_color=t["text"],
            command=lambda: self._add_kv_row(self._headers_scroll, self._headers_rows)
        ).pack(pady=4)

    def _build_params_tab(self):
        frame = self.tab_view.tab("Params")
        t = self.theme
        self._params_rows: list[tuple] = []
        self._params_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._params_scroll.pack(fill="both", expand=True)
        ctk.CTkButton(
            frame, text="+ Param", fg_color=t["surface2"],
            hover_color=t["border"], text_color=t["text"],
            command=lambda: self._add_kv_row(self._params_scroll, self._params_rows)
        ).pack(pady=4)

    def _add_kv_row(self, scroll, rows: list, key="", value=""):
        t = self.theme
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        k_var = ctk.StringVar(value=key)
        v_var = ctk.StringVar(value=value)
        ctk.CTkEntry(
            row, textvariable=k_var, placeholder_text="Chave",
            fg_color=t["surface2"], border_color=t["border"],
            text_color=t["text"], width=160
        ).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(
            row, textvariable=v_var, placeholder_text="Valor",
            fg_color=t["surface2"], border_color=t["border"],
            text_color=t["text"], width=220
        ).pack(side="left", padx=(0, 4))
        entry = (k_var, v_var, row)
        rows.append(entry)
        ctk.CTkButton(
            row, text="✕", width=28, fg_color="transparent",
            hover_color=t["error"], text_color=t["text_dim"],
            command=lambda: self._remove_row(rows, entry)
        ).pack(side="left")

    def _remove_row(self, rows: list, entry: tuple):
        entry[2].destroy()
        rows.remove(entry)

    def _build_body_tab(self):
        frame = self.tab_view.tab("Body")
        t = self.theme
        type_row = ctk.CTkFrame(frame, fg_color="transparent")
        type_row.pack(fill="x", pady=(4, 0))
        self.body_type_var = ctk.StringVar(value="json")
        for btype in ["json", "xml", "form", "raw"]:
            ctk.CTkRadioButton(
                type_row, text=btype, value=btype, variable=self.body_type_var,
                text_color=t["text"], fg_color=t["accent"]
            ).pack(side="left", padx=8)
        self.body_text = ctk.CTkTextbox(
            frame, fg_color=t["surface2"], text_color=t["text"],
            font=("JetBrains Mono", 12), border_color=t["border"], border_width=1
        )
        self.body_text.pack(fill="both", expand=True, pady=4)

    def _build_auth_tab(self):
        frame = self.tab_view.tab("Auth")
        t = self.theme
        self.auth_type_var = ctk.StringVar(value="none")
        ctk.CTkOptionMenu(
            frame, values=["none", "bearer", "basic", "api_key"],
            variable=self.auth_type_var,
            fg_color=t["surface2"], button_color=t["accent2"],
            text_color=t["text"], command=self._update_auth_ui
        ).pack(padx=12, pady=8, anchor="w")
        self._auth_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._auth_frame.pack(fill="both", expand=True, padx=12)
        self._auth_fields: dict[str, ctk.StringVar] = {}
        self._update_auth_ui("none")

    def _update_auth_ui(self, auth_type: str):
        for w in self._auth_frame.winfo_children():
            w.destroy()
        self._auth_fields = {}
        t = self.theme
        configs = {
            "bearer": [("Token", "token", False)],
            "basic": [("Usuário", "username", False), ("Senha", "password", True)],
            "api_key": [("Header", "header", False), ("Valor", "value", True)],
        }
        for label, key, secret in configs.get(auth_type, []):
            row = ctk.CTkFrame(self._auth_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, text_color=t["text_dim"], width=80).pack(side="left")
            var = ctk.StringVar()
            ctk.CTkEntry(
                row, textvariable=var, show="●" if secret else "",
                fg_color=t["surface2"], border_color=t["border"],
                text_color=t["text"]
            ).pack(side="left", fill="x", expand=True)
            self._auth_fields[key] = var

    def _update_method_color(self, method: str):
        pass

    def get_request_data(self) -> dict:
        return {
            "id": self._current_id,
            "name": self.name_var.get(),
            "method": self.method_var.get(),
            "url": self.url_var.get(),
            "headers": {r[0].get(): r[1].get() for r in self._headers_rows if r[0].get()},
            "params": {r[0].get(): r[1].get() for r in self._params_rows if r[0].get()},
            "body": self.body_text.get("1.0", "end-1c"),
            "body_type": self.body_type_var.get(),
            "auth_type": self.auth_type_var.get(),
            "auth_data": {k: v.get() for k, v in self._auth_fields.items()},
        }

    def load_request(self, data: dict):
        self._current_id = data.get("id")
        self.name_var.set(data.get("name", ""))
        self.method_var.set(data.get("method", "GET"))
        self.url_var.set(data.get("url", ""))
        self.body_type_var.set(data.get("body_type", "json"))

        for _, _, frame in self._headers_rows:
            frame.destroy()
        self._headers_rows.clear()
        for k, v in json.loads(data.get("headers", "{}") or "{}").items():
            self._add_kv_row(self._headers_scroll, self._headers_rows, k, v)

        for _, _, frame in self._params_rows:
            frame.destroy()
        self._params_rows.clear()
        for k, v in json.loads(data.get("params", "{}") or "{}").items():
            self._add_kv_row(self._params_scroll, self._params_rows, k, v)

        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", data.get("body", ""))

        self.auth_type_var.set(data.get("auth_type", "none"))
        self._update_auth_ui(data.get("auth_type", "none"))
        for k, v in json.loads(data.get("auth_data", "{}") or "{}").items():
            if k in self._auth_fields:
                self._auth_fields[k].set(v)

    def _send(self):
        self.on_send(self.get_request_data())

    def _save(self):
        self.on_save(self.get_request_data())
'''

# ── ui/response_panel.py ──────────────────────────────────────────────────────
FILES["ui/response_panel.py"] = '''\
import customtkinter as ctk
import json
from ui.styles import DARK, status_color


class ResponsePanel(ctk.CTkFrame):
    def __init__(self, master, theme=DARK, **kwargs):
        super().__init__(master, fg_color=theme["bg"], **kwargs)
        self.theme = theme
        self._build()

    def _build(self):
        t = self.theme

        self.status_bar = ctk.CTkFrame(self, fg_color=t["surface"], corner_radius=8, height=40)
        self.status_bar.pack(fill="x", padx=12, pady=(4, 4))
        self.status_bar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self.status_bar, text="—", font=("JetBrains Mono", 13, "bold"),
            text_color=t["text_dim"]
        )
        self.lbl_status.pack(side="left", padx=12)

        self.lbl_time = ctk.CTkLabel(
            self.status_bar, text="", font=("JetBrains Mono", 11),
            text_color=t["text_dim"]
        )
        self.lbl_time.pack(side="left", padx=8)

        self.lbl_size = ctk.CTkLabel(
            self.status_bar, text="", font=("JetBrains Mono", 11),
            text_color=t["text_dim"]
        )
        self.lbl_size.pack(side="left", padx=8)

        ctk.CTkButton(
            self.status_bar, text="⬇ Salvar", fg_color=t["surface2"],
            hover_color=t["border"], text_color=t["text"],
            width=80, command=self._save_response
        ).pack(side="right", padx=8, pady=4)

        self.tab_view = ctk.CTkTabview(
            self, fg_color=t["surface"],
            segmented_button_fg_color=t["surface2"],
            segmented_button_selected_color=t["accent"],
            segmented_button_selected_hover_color=t["accent2"],
            segmented_button_unselected_color=t["surface2"],
            text_color=t["text"]
        )
        self.tab_view.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tab_view.add("Body")
        self.tab_view.add("Headers")

        self.body_text = ctk.CTkTextbox(
            self.tab_view.tab("Body"), fg_color=t["surface2"],
            text_color=t["text"], font=("JetBrains Mono", 12),
            border_color=t["border"], border_width=1, wrap="none"
        )
        self.body_text.pack(fill="both", expand=True, padx=4, pady=4)

        self.headers_text = ctk.CTkTextbox(
            self.tab_view.tab("Headers"), fg_color=t["surface2"],
            text_color=t["text"], font=("JetBrains Mono", 12),
            border_color=t["border"], border_width=1
        )
        self.headers_text.pack(fill="both", expand=True, padx=4, pady=4)

        self._raw = ""

    def show_loading(self):
        self.body_text.configure(state="normal")
        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", "⏳ Enviando requisição...")
        self.body_text.configure(state="disabled")

    def show_result(self, result: dict):
        t = self.theme

        if not result["success"]:
            self.lbl_status.configure(text="ERRO", text_color=t["error"])
            self.lbl_time.configure(text=f"{result[\'elapsed_ms\']} ms")
            self._set_body(f"❌ {result.get(\'error\', \'Erro desconhecido\')}")
            return

        code = result["status_code"]
        color = status_color(code)
        self.lbl_status.configure(text=f"● {code}", text_color=color)
        self.lbl_time.configure(text=f"{result[\'elapsed_ms\']} ms", text_color=t["text_dim"])
        self.lbl_size.configure(
            text=f"{round(result[\'size\'] / 1024, 2)} KB", text_color=t["text_dim"]
        )

        if result["body"] is not None:
            pretty = json.dumps(result["body"], indent=2, ensure_ascii=False)
        else:
            pretty = result["raw"]
        self._raw = result["raw"]
        self._set_body(pretty)

        headers_text = "\\n".join(f"{k}: {v}" for k, v in result["headers"].items())
        self.headers_text.configure(state="normal")
        self.headers_text.delete("1.0", "end")
        self.headers_text.insert("1.0", headers_text)
        self.headers_text.configure(state="disabled")

    def _set_body(self, text: str):
        self.body_text.configure(state="normal")
        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", text)
        self.body_text.configure(state="disabled")

    def _save_response(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._raw)
'''

# ── ui/environment_dialog.py ──────────────────────────────────────────────────
FILES["ui/environment_dialog.py"] = '''\
import customtkinter as ctk
import json
from tkinter import filedialog, messagebox
from backend.env_manager import EnvManager
from ui.styles import DARK


class EnvironmentDialog(ctk.CTkToplevel):
    def __init__(self, master, env_manager: EnvManager, on_change, theme=DARK):
        super().__init__(master)
        self.title("🌍 Ambientes")
        self.geometry("720x500")
        self.env = env_manager
        self.on_change = on_change
        self.theme = theme
        self.configure(fg_color=theme["bg"])
        self._selected_env_id: int | None = None
        self._build()
        self._refresh_env_list()

    def _build(self):
        t = self.theme
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=16)

        left = ctk.CTkFrame(main, fg_color=t["surface"], width=200, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        ctk.CTkLabel(
            left, text="Ambientes", font=("JetBrains Mono", 13, "bold"),
            text_color=t["text"]
        ).pack(pady=8)

        self._env_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._env_scroll.pack(fill="both", expand=True, padx=4)

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=4)

        ctk.CTkButton(
            btn_row, text="+ Novo", fg_color=t["accent2"], text_color="white",
            command=self._new_env
        ).pack(side="left", expand=True, padx=2)

        ctk.CTkButton(
            btn_row, text="🗑", fg_color=t["surface2"], text_color=t["error"],
            width=36, command=self._delete_env
        ).pack(side="left", padx=2)

        right = ctk.CTkFrame(main, fg_color=t["surface"], corner_radius=8)
        right.pack(side="left", fill="both", expand=True)

        top_right = ctk.CTkFrame(right, fg_color="transparent")
        top_right.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(
            top_right, text="Variáveis", font=("JetBrains Mono", 13, "bold"),
            text_color=t["text"]
        ).pack(side="left")

        ctk.CTkButton(
            top_right, text="📥 Importar", fg_color=t["surface2"],
            text_color=t["text"], width=90, command=self._import
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            top_right, text="📤 Exportar", fg_color=t["surface2"],
            text_color=t["text"], width=90, command=self._export
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            top_right, text="+ Variável", fg_color=t["accent"],
            text_color="white", width=90, command=self._add_variable
        ).pack(side="right", padx=4)

        self._vars_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._vars_scroll.pack(fill="both", expand=True, padx=8, pady=4)

    def _refresh_env_list(self):
        for w in self._env_scroll.winfo_children():
            w.destroy()
        t = self.theme
        for e in self.env.list_environments():
            row = ctk.CTkFrame(self._env_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            is_active = e["is_active"]
            ctk.CTkButton(
                row,
                text=f"{\\'✓ \\' if is_active else \\'  \\'}{e[\\'name\\']}",
                fg_color=t["accent2"] if is_active else t["surface2"],
                hover_color=t["border"], text_color=t["text"], anchor="w",
                command=lambda eid=e["id"]: self._select_env(eid)
            ).pack(side="left", fill="x", expand=True, padx=(0, 4))
            ctk.CTkButton(
                row, text="▶", width=28,
                fg_color=t["success"] if not is_active else t["surface2"],
                text_color="white" if not is_active else t["text_dim"],
                command=lambda eid=e["id"]: self._activate_env(eid)
            ).pack(side="left")

    def _refresh_vars(self):
        for w in self._vars_scroll.winfo_children():
            w.destroy()
        if not self._selected_env_id:
            return
        t = self.theme
        for var in self.env.get_variables(self._selected_env_id):
            row = ctk.CTkFrame(self._vars_scroll, fg_color=t["surface2"], corner_radius=6)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text="{{" + var["key"] + "}}", font=("JetBrains Mono", 11, "bold"),
                text_color=t["accent"], width=160, anchor="w"
            ).pack(side="left", padx=8)
            display = "●●●●●●" if var["is_secret"] else var["value"]
            ctk.CTkLabel(
                row, text=display, text_color=t["text_dim"], font=("JetBrains Mono", 11)
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="✏", width=28, fg_color="transparent",
                hover_color=t["border"], text_color=t["text"],
                command=lambda v=var: self._edit_variable(v)
            ).pack(side="right", padx=2)
            ctk.CTkButton(
                row, text="✕", width=28, fg_color="transparent",
                hover_color=t["error"], text_color=t["error"],
                command=lambda vid=var["id"]: self._delete_variable(vid)
            ).pack(side="right", padx=2)

    def _select_env(self, env_id: int):
        self._selected_env_id = env_id
        self._refresh_vars()

    def _activate_env(self, env_id: int):
        self.env.set_active_environment(env_id)
        self.on_change()
        self._refresh_env_list()

    def _new_env(self):
        dialog = ctk.CTkInputDialog(text="Nome do ambiente:", title="Novo Ambiente")
        name = dialog.get_input()
        if name:
            self.env.create_environment(name)
            self._refresh_env_list()

    def _delete_env(self):
        if self._selected_env_id:
            self.env.delete_environment(self._selected_env_id)
            self._selected_env_id = None
            self._refresh_env_list()
            self._refresh_vars()

    def _add_variable(self):
        if not self._selected_env_id:
            messagebox.showwarning("MiauBox", "Selecione um ambiente primeiro.")
            return
        self._variable_form()

    def _edit_variable(self, var: dict):
        self._variable_form(var)

    def _variable_form(self, var: dict | None = None):
        t = self.theme
        win = ctk.CTkToplevel(self)
        win.title("Variável")
        win.geometry("400x240")
        win.configure(fg_color=t["bg"])
        key_var = ctk.StringVar(value=var["key"] if var else "")
        val_var = ctk.StringVar(value=var["value"] if var else "")
        secret_var = ctk.BooleanVar(value=var["is_secret"] if var else False)
        for label, sv, secret in [("Chave", key_var, False), ("Valor", val_var, True)]:
            row = ctk.CTkFrame(win, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=label, text_color=t["text"], width=60).pack(side="left")
            ctk.CTkEntry(
                row, textvariable=sv,
                show="●" if (secret and secret_var.get()) else "",
                fg_color=t["surface2"], border_color=t["border"], text_color=t["text"]
            ).pack(side="left", fill="x", expand=True)
        ctk.CTkCheckBox(
            win, text="Valor secreto", variable=secret_var,
            text_color=t["text"], fg_color=t["accent"]
        ).pack(padx=16, pady=4, anchor="w")

        def save():
            self.env.upsert_variable(
                self._selected_env_id, key_var.get(), val_var.get(), secret_var.get()
            )
            self._refresh_vars()
            win.destroy()

        ctk.CTkButton(
            win, text="Salvar", fg_color=t["accent"], text_color="white", command=save
        ).pack(pady=8)

    def _delete_variable(self, var_id: int):
        self.env.delete_variable(var_id)
        self._refresh_vars()

    def _export(self):
        if not self._selected_env_id:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.env.export_environment(self._selected_env_id))

    def _import(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            with open(path, encoding="utf-8") as f:
                self.env.import_environment(f.read())
            self._refresh_env_list()
'''

# ── ui/history_window.py ──────────────────────────────────────────────────────
FILES["ui/history_window.py"] = '''\
import customtkinter as ctk
from backend.database import get_session, RequestHistory
from ui.styles import DARK, METHOD_COLORS, status_color


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master, theme=DARK, on_load=None):
        super().__init__(master)
        self.title("🕑 Histórico")
        self.geometry("800x500")
        self.configure(fg_color=theme["bg"])
        self.theme = theme
        self.on_load = on_load
        self._build()
        self._load()

    def _build(self):
        t = self.theme
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=t["surface"])
        self.scroll.pack(fill="both", expand=True, padx=12, pady=12)

    def _load(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        t = self.theme
        session = get_session()
        try:
            records = (
                session.query(RequestHistory)
                .order_by(RequestHistory.executed_at.desc())
                .limit(100)
                .all()
            )
            for rec in records:
                row = ctk.CTkFrame(self.scroll, fg_color=t["surface2"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=4)
                method_color = METHOD_COLORS.get(rec.method, t["text_dim"])
                ctk.CTkLabel(
                    row, text=rec.method, text_color=method_color,
                    font=("JetBrains Mono", 10, "bold"), width=50
                ).pack(side="left", padx=8)
                ctk.CTkLabel(
                    row, text=rec.url[:60], text_color=t["text"],
                    font=("JetBrains Mono", 11), anchor="w"
                ).pack(side="left", fill="x", expand=True)
                sc = rec.status_code or 0
                ctk.CTkLabel(
                    row, text=str(sc), text_color=status_color(sc),
                    font=("JetBrains Mono", 11, "bold"), width=45
                ).pack(side="left")
                ctk.CTkLabel(
                    row, text=f"{rec.response_time} ms", text_color=t["text_dim"],
                    font=("JetBrains Mono", 10), width=70
                ).pack(side="left", padx=4)
                ctk.CTkLabel(
                    row,
                    text=rec.executed_at.strftime("%d/%m %H:%M") if rec.executed_at else "",
                    text_color=t["text_dim"], font=("JetBrains Mono", 10), width=80
                ).pack(side="left", padx=4)
                if self.on_load:
                    ctk.CTkButton(
                        row, text="↩ Usar", width=60,
                        fg_color=t["accent2"], text_color="white",
                        command=lambda r=rec: self._use(r)
                    ).pack(side="right", padx=4, pady=4)
        finally:
            session.close()

    def _use(self, rec: RequestHistory):
        if self.on_load:
            self.on_load({
                "name": f"[Histórico] {rec.method} {rec.url[:30]}",
                "method": rec.method,
                "url": rec.url,
                "headers": "{}",
                "params": "{}",
                "body": rec.request_data or "",
                "body_type": "json",
                "auth_type": "none",
                "auth_data": "{}",
            })
        self.destroy()
'''

# ── ui/app.py ─────────────────────────────────────────────────────────────────
FILES["ui/app.py"] = '''\
import customtkinter as ctk
import json
import threading
from backend.database import get_session, SavedRequest
from backend.env_manager import EnvManager
from backend.request_runner import RequestRunner
from ui.sidebar import Sidebar
from ui.request_panel import RequestPanel
from ui.response_panel import ResponsePanel
from ui.environment_dialog import EnvironmentDialog
from ui.styles import DARK, LIGHT


class MiauBoxApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("MiauBox 🐱")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=DARK["bg"])
        self._theme = DARK
        self._env_manager = EnvManager()
        self._runner = RequestRunner(self._env_manager)
        self._build()

    def _get_env_names(self) -> list[str]:
        return [e["name"] for e in self._env_manager.list_environments()] or ["Nenhum"]

    def _build(self):
        t = self._theme

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self, fg_color=t["surface"], height=48, corner_radius=0)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        ctk.CTkLabel(
            topbar, text="🐱 MiauBox", font=("JetBrains Mono", 16, "bold"),
            text_color=t["accent"]
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            topbar, text="Ambiente:", text_color=t["text_dim"],
            font=("JetBrains Mono", 11)
        ).pack(side="left", padx=(40, 4))

        self._env_names = self._get_env_names()
        self._env_var = ctk.StringVar(value=self._env_manager.get_active_env_name())

        self._env_dropdown = ctk.CTkOptionMenu(
            topbar, values=self._env_names,
            variable=self._env_var,
            fg_color=t["surface2"], button_color=t["accent2"],
            dropdown_fg_color=t["surface"], text_color=t["text"],
            command=self._switch_env
        )
        self._env_dropdown.pack(side="left", padx=4)

        ctk.CTkButton(
            topbar, text="⚙ Ambientes", fg_color=t["surface2"],
            hover_color=t["border"], text_color=t["text"],
            command=self._open_env_dialog
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            topbar, text="☀/🌙", width=50,
            fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"],
            command=self._toggle_theme
        ).pack(side="right", padx=8)

        # ── Main layout ───────────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        self.sidebar = Sidebar(main, on_load_request=self._load_request, theme=t)
        self.sidebar.pack(side="left", fill="y")

        center = ctk.CTkFrame(main, fg_color=t["bg"])
        center.pack(side="left", fill="both", expand=True)

        self.request_panel = RequestPanel(
            center, on_send=self._send_request, on_save=self._save_request,
            env_manager=self._env_manager, theme=t
        )
        self.request_panel.pack(fill="both", expand=True, side="top")

        separator = ctk.CTkFrame(center, fg_color=t["border"], height=2)
        separator.pack(fill="x")

        self.response_panel = ResponsePanel(center, theme=t)
        self.response_panel.pack(fill="both", expand=True, side="top")

    def _send_request(self, data: dict):
        self.response_panel.show_loading()

        def run():
            result = self._runner.run(
                method=data["method"],
                url=data["url"],
                headers=data

                headers=data["headers"],
                params=data["params"],
                body=data["body"],
                body_type=data["body_type"],
                auth_type=data["auth_type"],
                auth_data=data["auth_data"],
            )
            self.after(0, lambda: self.response_panel.show_result(result))

        threading.Thread(target=run, daemon=True).start()

    def _save_request(self, data: dict):
        session = get_session()
        try:
            request_id = data.get("id")
            if request_id:
                req = session.query(SavedRequest).filter_by(id=request_id).first()
            else:
                req = None

            if req:
                req.name = data["name"]
                req.method = data["method"]
                req.url = data["url"]
                req.headers = json.dumps(data["headers"], ensure_ascii=False)
                req.params = json.dumps(data["params"], ensure_ascii=False)
                req.body = data["body"]
                req.body_type = data["body_type"]
                req.auth_type = data["auth_type"]
                req.auth_data = json.dumps(data["auth_data"], ensure_ascii=False)
            else:
                req = SavedRequest(
                    name=data["name"],
                    method=data["method"],
                    url=data["url"],
                    headers=json.dumps(data["headers"], ensure_ascii=False),
                    params=json.dumps(data["params"], ensure_ascii=False),
                    body=data["body"],
                    body_type=data["body_type"],
                    auth_type=data["auth_type"],
                    auth_data=json.dumps(data["auth_data"], ensure_ascii=False),
                )
                session.add(req)

            session.commit()
            session.refresh(req)
            data["id"] = req.id
            self.request_panel._current_id = req.id
            self.sidebar.refresh()
        finally:
            session.close()

    def _load_request(self, data: dict):
        self.request_panel.load_request(data)

    def _switch_env(self, selected_name: str):
        envs = self._env_manager.list_environments()
        for env in envs:
            if env["name"] == selected_name:
                self._env_manager.set_active_environment(env["id"])
                break
        self._env_var.set(self._env_manager.get_active_env_name())
        self.sidebar.refresh()

    def _open_env_dialog(self):
        def on_change():
            self._env_names = self._get_env_names()
            self._env_dropdown.configure(values=self._env_names)
            self._env_var.set(self._env_manager.get_active_env_name())
            self.sidebar.refresh()

        EnvironmentDialog(self, self._env_manager, on_change, theme=self._theme)

    def _toggle_theme(self):
        if self._theme == DARK:
            self._theme = LIGHT
            ctk.set_appearance_mode("light")
            self.configure(fg_color=LIGHT["bg"])
        else:
            self._theme = DARK
            ctk.set_appearance_mode("dark")
            self.configure(fg_color=DARK["bg"])

    def run(self):
        self.mainloop()
'''

FILES["main.py"] = '''\
from backend.database import init_db
from ui.app import MiauBoxApp


def main():
    init_db()
    app = MiauBoxApp()
    app.run()


if __name__ == "__main__":
    main()
'''

# ── Escrita dos arquivos ─────────────────────────────────────────────────────
def write_files(base_dir="."):
    for relative_path, content in FILES.items():
        path = os.path.join(base_dir, relative_path)
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"{len(FILES)} arquivos criados com sucesso.")


if __name__ == "__main__":
    write_files()
# %%
