import customtkinter as ctk
import json


class RequestPanel(ctk.CTkFrame):
    def __init__(self, master, on_send, on_save, env_manager, theme, **kwargs):
        super().__init__(master, fg_color=theme["bg"], **kwargs)
        self.theme = theme
        self.on_send = on_send
        self.on_save = on_save
        self.env = env_manager
        self._current_id = None
        self.details_visible = True
        self._build()

    def _build(self):
        t = self.theme

        # ── Barra compacta superior ───────────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, fg_color=t["surface"], corner_radius=8)
        self.top_bar.pack(fill="x", padx=12, pady=(12, 6))

        self.method_var = ctk.StringVar(value="GET")
        ctk.CTkOptionMenu(
            self.top_bar,
            values=["GET", "POST", "PUT", "PATCH", "DELETE"],
            variable=self.method_var,
            width=100,
            fg_color=t["surface2"],
            button_color=t["accent2"],
            dropdown_fg_color=t["surface"],
            text_color=t["text"],
        ).pack(side="left", padx=(8, 4), pady=8)

        self.url_var = ctk.StringVar()
        ctk.CTkEntry(
            self.top_bar,
            textvariable=self.url_var,
            placeholder_text="https://api.exemplo.com/endpoint",
            fg_color=t["surface2"],
            border_color=t["border"],
            text_color=t["text"],
            font=("JetBrains Mono", 13),
        ).pack(side="left", fill="x", expand=True, padx=4, pady=8)

        ctk.CTkButton(
            self.top_bar,
            text="▶ Enviar",
            fg_color=t["accent"],
            hover_color=t["accent2"],
            text_color="white",
            font=("JetBrains Mono", 13, "bold"),
            width=100,
            command=self._send,
        ).pack(side="left", padx=(4, 4), pady=8)

        ctk.CTkButton(
            self.top_bar,
            text="💾 Salvar",
            fg_color=t["surface2"],
            hover_color=t["border"],
            text_color=t["text"],
            width=90,
            command=self._save,
        ).pack(side="left", padx=(0, 4), pady=8)

        self.details_btn = ctk.CTkButton(
            self.top_bar,
            text="▾ Detalhes",
            fg_color=t["surface2"],
            hover_color=t["border"],
            text_color=t["text"],
            width=110,
            command=self._toggle_details,
        )
        self.details_btn.pack(side="left", padx=(0, 8), pady=8)

        # ── Área de detalhes ──────────────────────────────────────────────────
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Nome
        name_row = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=0, pady=(0, 4))

        self.name_var = ctk.StringVar(value="Nova Requisição")
        ctk.CTkEntry(
            name_row,
            textvariable=self.name_var,
            fg_color="transparent",
            border_width=0,
            text_color=t["text_dim"],
            font=("JetBrains Mono", 11),
        ).pack(side="left", fill="x", expand=True)

        # Tabs
        self.tab_view = ctk.CTkTabview(
            self.details_frame,
            fg_color=t["surface"],
            segmented_button_fg_color=t["surface2"],
            segmented_button_selected_color=t["accent"],
            segmented_button_selected_hover_color=t["accent2"],
            segmented_button_unselected_color=t["surface2"],
            text_color=t["text"],
        )
        self.tab_view.pack(fill="both", expand=True, padx=0, pady=4)

        for tab in ["Headers", "Params", "Body", "Auth", "Script"]:
            self.tab_view.add(tab)

        self._build_headers_tab()
        self._build_params_tab()
        self._build_body_tab()
        self._build_auth_tab()
        self._build_script_tab()

    def _toggle_details(self):
        t = self.theme

        if self.details_visible:
            self.details_frame.pack_forget()
            self.details_btn.configure(text="▸ Detalhes")
            self.details_visible = False
        else:
            self.details_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            self.details_btn.configure(text="▾ Detalhes")
            self.details_visible = True

    # ── Headers Tab ────────────────────────────────────────────────────────
    def _build_headers_tab(self):
        frame = self.tab_view.tab("Headers")
        t = self.theme
        self._headers_rows = []

        self._headers_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._headers_scroll.pack(fill="both", expand=True)

        ctk.CTkButton(
            frame,
            text="+ Header",
            fg_color=t["surface2"],
            hover_color=t["border"],
            text_color=t["text"],
            command=lambda: self._add_kv_row(self._headers_scroll, self._headers_rows),
        ).pack(pady=4)

    # ── Params Tab ─────────────────────────────────────────────────────────
    def _build_params_tab(self):
        frame = self.tab_view.tab("Params")
        t = self.theme
        self._params_rows = []

        self._params_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._params_scroll.pack(fill="both", expand=True)

        ctk.CTkButton(
            frame,
            text="+ Param",
            fg_color=t["surface2"],
            hover_color=t["border"],
            text_color=t["text"],
            command=lambda: self._add_kv_row(self._params_scroll, self._params_rows),
        ).pack(pady=4)

    def _add_kv_row(self, scroll, rows, key="", value=""):
        t = self.theme

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)

        k_var = ctk.StringVar(value=key)
        v_var = ctk.StringVar(value=value)

        ctk.CTkEntry(
            row,
            textvariable=k_var,
            placeholder_text="Chave",
            fg_color=t["surface2"],
            border_color=t["border"],
            text_color=t["text"],
            width=160,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkEntry(
            row,
            textvariable=v_var,
            placeholder_text="Valor",
            fg_color=t["surface2"],
            border_color=t["border"],
            text_color=t["text"],
            width=220,
        ).pack(side="left", padx=(0, 4))

        entry = (k_var, v_var, row)
        rows.append(entry)

        ctk.CTkButton(
            row,
            text="✕",
            width=28,
            fg_color="transparent",
            hover_color=t["error"],
            text_color=t["text_dim"],
            command=lambda: self._remove_row(rows, entry),
        ).pack(side="left")

    def _remove_row(self, rows, entry):
        entry[2].destroy()
        rows.remove(entry)

    # ── Body Tab ───────────────────────────────────────────────────────────
    def _build_body_tab(self):
        frame = self.tab_view.tab("Body")
        t = self.theme

        type_row = ctk.CTkFrame(frame, fg_color="transparent")
        type_row.pack(fill="x", pady=(4, 0))

        self.body_type_var = ctk.StringVar(value="json")
        for btype in ["json", "xml", "form", "raw"]:
            ctk.CTkRadioButton(
                type_row,
                text=btype,
                value=btype,
                variable=self.body_type_var,
                text_color=t["text"],
                fg_color=t["accent"],
            ).pack(side="left", padx=8)

        self.body_text = ctk.CTkTextbox(
            frame,
            fg_color=t["surface2"],
            text_color=t["text"],
            font=("JetBrains Mono", 12),
            border_color=t["border"],
            border_width=1,
        )
        self.body_text.pack(fill="both", expand=True, pady=4)

    # ── Auth Tab ───────────────────────────────────────────────────────────
    def _build_auth_tab(self):
        frame = self.tab_view.tab("Auth")
        t = self.theme

        self.auth_type_var = ctk.StringVar(value="none")
        ctk.CTkOptionMenu(
            frame,
            values=["none", "bearer", "basic", "api_key"],
            variable=self.auth_type_var,
            fg_color=t["surface2"],
            button_color=t["accent2"],
            text_color=t["text"],
            command=self._update_auth_ui,
        ).pack(padx=12, pady=8, anchor="w")

        self._auth_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._auth_frame.pack(fill="both", expand=True, padx=12)

        self._auth_fields = {}
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

            ctk.CTkLabel(
                row,
                text=label,
                text_color=t["text_dim"],
                width=80,
            ).pack(side="left")

            var = ctk.StringVar()
            ctk.CTkEntry(
                row,
                textvariable=var,
                show="●" if secret else "",
                fg_color=t["surface2"],
                border_color=t["border"],
                text_color=t["text"],
            ).pack(side="left", fill="x", expand=True)

            self._auth_fields[key] = var

    def _build_script_tab(self):
        frame = self.tab_view.tab("Script")
        t = self.theme

        # ── Pré-requisição ────────────────────────────────────
        pre_header = ctk.CTkFrame(frame, fg_color=t["surface2"], corner_radius=6)
        pre_header.pack(fill="x", padx=4, pady=(6, 0))

        ctk.CTkLabel(
            pre_header,
            text="⚡ Pré-requisição",
            font=("JetBrains Mono", 11, "bold"),
            text_color=t["accent"]
        ).pack(side="left", padx=10, pady=6)

        ctk.CTkLabel(
            pre_header,
            text="Variáveis disponíveis:  request  •  env",
            font=("JetBrains Mono", 10),
            text_color=t["text_dim"]
        ).pack(side="right", padx=10)

        self.pre_script_text = ctk.CTkTextbox(
            frame, fg_color=t["surface2"], text_color=t["text"],
            font=("JetBrains Mono", 12), border_color=t["border"],
            border_width=1, height=120
        )
        self.pre_script_text.pack(fill="x", padx=4, pady=(2, 8))
        self.pre_script_text.insert("1.0", "# Executado antes do envio\n# Exemplo:\n# request.headers[\"X-Timestamp\"] = \"2024-01-01\"\n# env[\"MY_VAR\"] = \"valor\"\n")

        # ── Pós-requisição ────────────────────────────────────
        pos_header = ctk.CTkFrame(frame, fg_color=t["surface2"], corner_radius=6)
        pos_header.pack(fill="x", padx=4, pady=(0, 0))

        ctk.CTkLabel(
            pos_header,
            text="✅ Pós-requisição",
            font=("JetBrains Mono", 11, "bold"),
            text_color=t["success"]
        ).pack(side="left", padx=10, pady=6)

        ctk.CTkLabel(
            pos_header,
            text="Variáveis disponíveis:  request  •  response  •  env",
            font=("JetBrains Mono", 10),
            text_color=t["text_dim"]
        ).pack(side="right", padx=10)

        self.pos_script_text = ctk.CTkTextbox(
            frame, fg_color=t["surface2"], text_color=t["text"],
            font=("JetBrains Mono", 12), border_color=t["border"],
            border_width=1, height=120
        )
        self.pos_script_text.pack(fill="x", padx=4, pady=(2, 8))
        self.pos_script_text.insert("1.0", "# Executado após receber a resposta\n# Exemplo:\n# if response.status_code == 200:\n#     env[\"TOKEN\"] = response.json()[\"token\"]\n")

        # ── Log de execução ───────────────────────────────────
        ctk.CTkLabel(
            frame, text="📋 Log de execução",
            font=("JetBrains Mono", 11, "bold"),
            text_color=t["text_dim"]
        ).pack(anchor="w", padx=4, pady=(4, 0))

        self.script_log_text = ctk.CTkTextbox(
            frame, fg_color=t["bg"], text_color=t["text_dim"],
            font=("JetBrains Mono", 11), border_color=t["border"],
            border_width=1, height=80, state="disabled"
        )
        self.script_log_text.pack(fill="x", padx=4, pady=(2, 4))

    # ── Dados da request ───────────────────────────────────────────────────
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
            "pre_script": self.pre_script_text.get("1.0", "end-1c"),
            "pos_script": self.pos_script_text.get("1.0", "end-1c"),
        }

    def load_request(self, data: dict):
        self._current_id = data.get("id")
        self.name_var.set(data.get("name", ""))
        self.method_var.set(data.get("method", "GET"))
        self.url_var.set(data.get("url", ""))
        self.body_type_var.set(data.get("body_type", "json"))

        # Headers
        for _, _, frame in self._headers_rows:
            frame.destroy()
        self._headers_rows.clear()
        for k, v in json.loads(data.get("headers", "{}") or "{}").items():
            self._add_kv_row(self._headers_scroll, self._headers_rows, k, v)

        # Params
        for _, _, frame in self._params_rows:
            frame.destroy()
        self._params_rows.clear()
        for k, v in json.loads(data.get("params", "{}") or "{}").items():
            self._add_kv_row(self._params_scroll, self._params_rows, k, v)

        # Body
        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", data.get("body", ""))

        # Auth
        self.auth_type_var.set(data.get("auth_type", "none"))
        self._update_auth_ui(data.get("auth_type", "none"))
        for k, v in json.loads(data.get("auth_data", "{}") or "{}").items():
            if k in self._auth_fields:
                self._auth_fields[k].set(v)

        # Scripts
        self.pre_script_text.delete("1.0", "end")
        self.pre_script_text.insert("1.0", data.get("pre_script", ""))

        self.pos_script_text.delete("1.0", "end")
        self.pos_script_text.insert("1.0", data.get("pos_script", ""))

    def write_script_log(self, text: str):
        self.script_log_text.configure(state="normal")
        self.script_log_text.delete("1.0", "end")
        self.script_log_text.insert("1.0", text)
        self.script_log_text.configure(state="disabled")
        
    def _send(self):
        self.on_send(self.get_request_data())

    def _save(self):
        self.on_save(self.get_request_data())