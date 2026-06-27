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

        # ── Lado esquerdo: lista de ambientes ─────────────
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

        # ── Lado direito: variáveis ────────────────────────
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
            prefix = "✓ " if is_active else "  "
            label = prefix + e["name"]

            ctk.CTkButton(
                row,
                text=label,
                fg_color=t["accent2"] if is_active else t["surface2"],
                hover_color=t["border"],
                text_color=t["text"],
                anchor="w",
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
                row, text="{{" + var["key"] + "}}",
                font=("JetBrains Mono", 11, "bold"),
                text_color=t["accent"], width=160, anchor="w"
            ).pack(side="left", padx=8)

            display = "●●●●●●" if var["is_secret"] else var["value"]
            ctk.CTkLabel(
                row, text=display, text_color=t["text_dim"],
                font=("JetBrains Mono", 11)
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
                fg_color=t["surface2"], border_color=t["border"],
                text_color=t["text"]
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
            win, text="Salvar", fg_color=t["accent"],
            text_color="white", command=save
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