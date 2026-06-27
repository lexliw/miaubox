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
            topbar, text="🐱 MiauBox",
            font=("JetBrains Mono", 16, "bold"),
            text_color=t["accent"]
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            topbar, text="Ambiente:",
            text_color=t["text_dim"],
            font=("JetBrains Mono", 11)
        ).pack(side="left", padx=(40, 4))

        self._env_names = self._get_env_names()
        self._env_var = ctk.StringVar(value=self._env_manager.get_active_env_name())

        self._env_dropdown = ctk.CTkOptionMenu(
            topbar,
            values=self._env_names,
            variable=self._env_var,
            fg_color=t["surface2"],
            button_color=t["accent2"],
            dropdown_fg_color=t["surface"],
            text_color=t["text"],
            command=self._switch_env
        )
        self._env_dropdown.pack(side="left", padx=4)

        ctk.CTkButton(
            topbar, text="⚙ Ambientes",
            fg_color=t["surface2"],
            hover_color=t["border"],
            text_color=t["text"],
            command=self._open_env_dialog
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            topbar, text="☀/🌙", width=50,
            fg_color=t["surface2"],
            hover_color=t["border"],
            text_color=t["text"],
            command=self._toggle_theme
        ).pack(side="right", padx=8)

        # ── Main layout ───────────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        self.sidebar = Sidebar(
            main,
            on_load_request=self._load_request,
            theme=t
        )
        self.sidebar.pack(side="left", fill="y")

        center = ctk.CTkFrame(main, fg_color=t["bg"])
        center.pack(side="left", fill="both", expand=True)

        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(1, weight=1)

        self.request_panel = RequestPanel(
            center,
            on_send=self._send_request,
            on_save=self._save_request,
            env_manager=self._env_manager,
            theme=t
        )
        self.request_panel.grid(row=0, column=0, sticky="ew")

        self.response_panel = ResponsePanel(center, theme=t)
        self.response_panel.grid(row=1, column=0, sticky="nsew")


    # ── Handlers ──────────────────────────────────────────────────────────────

    def _send_request(self, data: dict):
        self.response_panel.show_loading()

        def run():
            result = self._runner.run(
                method=data["method"],
                url=data["url"],
                headers=data["headers"],
                params=data["params"],
                body=data["body"],
                body_type=data["body_type"],
                auth_type=data["auth_type"],
                auth_data=data["auth_data"],
                pre_script=data.get("pre_script", ""),
                pos_script=data.get("pos_script", ""),
            )

            def update():
                self.response_panel.show_result(result)
                self.request_panel.write_script_log(result.get("script_log", ""))

            self.after(0, update)

        threading.Thread(target=run, daemon=True).start()

    def _save_request(self, data: dict):
        from backend.database import Collection
        session = get_session()
        try:
            # Se já tem ID, apenas atualiza
            request_id = data.get("id")
            if request_id:
                req = session.query(SavedRequest).filter_by(id=request_id).first()
                if req:
                    req.name       = data["name"]
                    req.method     = data["method"]
                    req.url        = data["url"]
                    req.headers    = json.dumps(data["headers"], ensure_ascii=False)
                    req.params     = json.dumps(data["params"], ensure_ascii=False)
                    req.body       = data["body"]
                    req.body_type  = data["body_type"]
                    req.auth_type  = data["auth_type"]
                    req.auth_data  = json.dumps(data["auth_data"], ensure_ascii=False)
                    req.pre_script = data.get("pre_script", "")   # ← adicionado
                    req.pos_script = data.get("pos_script", "")   # ← adicionado
                    session.commit()
                    session.refresh(req)
                    self.request_panel._current_id = req.id
                    self.sidebar.refresh()
                    return

            # Se não tem ID, pede coleção e nome
            collections = session.query(Collection).all()
            if not collections:
                from tkinter import messagebox
                messagebox.showwarning(
                    "MiauBox",
                    "Nenhuma coleção encontrada.\nCrie uma coleção na sidebar primeiro."
                )
                return

            col_names = [c.name for c in collections]
            col_map   = {c.name: c.id for c in collections}

        finally:
            session.close()

        # Diálogo para escolher coleção
        dialog_win = ctk.CTkToplevel(self)
        dialog_win.title("Salvar Requisição")
        dialog_win.geometry("400x260")
        dialog_win.configure(fg_color=self._theme["bg"])
        dialog_win.grab_set()

        t = self._theme

        ctk.CTkLabel(
            dialog_win, text="Nome da requisição:",
            text_color=t["text"], font=("JetBrains Mono", 12)
        ).pack(padx=20, pady=(20, 4), anchor="w")

        name_var = ctk.StringVar(value=data["name"])
        ctk.CTkEntry(
            dialog_win, textvariable=name_var,
            fg_color=t["surface2"], border_color=t["border"],
            text_color=t["text"]
        ).pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            dialog_win, text="Salvar na coleção:",
            text_color=t["text"], font=("JetBrains Mono", 12)
        ).pack(padx=20, pady=(0, 4), anchor="w")

        col_var = ctk.StringVar(value=col_names[0])
        ctk.CTkOptionMenu(
            dialog_win, values=col_names, variable=col_var,
            fg_color=t["surface2"], button_color=t["accent2"],
            dropdown_fg_color=t["surface"], text_color=t["text"]
        ).pack(fill="x", padx=20, pady=(0, 16))

        def confirm():
            session2 = get_session()
            try:
                req = SavedRequest(
                    name=name_var.get() or data["name"],
                    method=data["method"],
                    url=data["url"],
                    headers=json.dumps(data["headers"], ensure_ascii=False),
                    params=json.dumps(data["params"], ensure_ascii=False),
                    body=data["body"],
                    body_type=data["body_type"],
                    auth_type=data["auth_type"],
                    auth_data=json.dumps(data["auth_data"], ensure_ascii=False),
                    pre_script=data.get("pre_script", ""),   # ← adicionado
                    pos_script=data.get("pos_script", ""),   # ← adicionado
                    collection_id=col_map[col_var.get()],
                )
                session2.add(req)
                session2.commit()
                session2.refresh(req)
                self.request_panel._current_id = req.id
                self.sidebar.refresh()
            finally:
                session2.close()
            dialog_win.destroy()

        ctk.CTkButton(
            dialog_win, text="💾 Salvar",
            fg_color=t["accent"], hover_color=t["accent2"],
            text_color="white", command=confirm
        ).pack(pady=4)

    def _load_request(self, data: dict):
        self.request_panel.load_request(data)

    def _switch_env(self, selected_name: str):
        for env in self._env_manager.list_environments():
            if env["name"] == selected_name:
                self._env_manager.set_active_environment(env["id"])
                break
        self._env_var.set(self._env_manager.get_active_env_name())

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