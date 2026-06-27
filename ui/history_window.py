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
