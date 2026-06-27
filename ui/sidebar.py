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

        # header = ctk.CTkFrame(self, fg_color=self.theme["surface2"], corner_radius=0)
        # header.pack(fill="x", padx=0, pady=0)

        # ctk.CTkLabel(
        #     header, text="🐱📦 MiauBox", font=("JetBrains Mono", 18, "bold"),
        #     text_color=t["accent"]
        # ).pack(pady=12)

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
        arrow = "▾" if is_open else "▸"

        ctk.CTkButton(
            row, text=f"{arrow} 📁 {col.name}",
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
            "pre_script": req.pre_script or "",   # ← adicionado
            "pos_script": req.pos_script or "",   # ← adicionado
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
        from tkinter import messagebox
        session = get_session()
        try:
            col = session.query(Collection).filter_by(id=col_id).first()
            if not col:
                return

            confirm = messagebox.askyesno(
                "Deletar Coleção",
                f"Tem certeza que deseja deletar a coleção '{col.name}'?\n\nTodas as requisições dentro dela também serão deletadas.",
                icon="warning"
            )

            if confirm:
                session.delete(col)
                session.commit()
        finally:
            session.close()

        if confirm:
            self.refresh()

    def _show_history(self):
        from ui.history_window import HistoryWindow
        HistoryWindow(self, self.theme, self.on_load_request)