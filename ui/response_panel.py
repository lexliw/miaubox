from ui.syntax_highlight import highlight_json
import customtkinter as ctk
import json
from ui.styles import DARK, status_color
import re
import keyword


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
            self.lbl_time.configure(text=f"{result['elapsed_ms']} ms")
            self._set_body(f"❌ {result.get('error', 'Erro desconhecido')}")
            return

        code = result["status_code"]
        color = status_color(code)
        self.lbl_status.configure(text=f"● {code}", text_color=color)
        self.lbl_time.configure(text=f"{result['elapsed_ms']} ms", text_color=t["text_dim"])
        self.lbl_size.configure(
            text=f"{round(result['size'] / 1024, 2)} KB", text_color=t["text_dim"]
        )

        if result["body"] is not None:
            pretty = json.dumps(result["body"], indent=2, ensure_ascii=False)
        else:
            pretty = result["raw"]
        self._raw = result["raw"]
        self._set_body(pretty, json_mode=(result["body"] is not None))

        headers_text = "\n".join(f"{k}: {v}" for k, v in result["headers"].items())
        self.headers_text.configure(state="normal")
        self.headers_text.delete("1.0", "end")
        self.headers_text.insert("1.0", headers_text)
        self.headers_text.configure(state="disabled")

    def _set_body(self, text: str, json_mode: bool = False):
        self.body_text.configure(state="normal")
        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", text)

        self._highlighted_json = json_mode
        if json_mode:
            self._highlight_json(self.body_text)

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

    def _text_widget(self, widget):
        return getattr(widget, "_textbox", widget)

    def _setup_json_tags(self, widget):
        txt = self._text_widget(widget)
        txt.tag_configure("json_key",    foreground="#61AFEF")
        txt.tag_configure("json_string", foreground="#98C379")
        txt.tag_configure("json_number", foreground="#D19A66")
        txt.tag_configure("json_bool",   foreground="#C678DD")
        txt.tag_configure("json_null",   foreground="#E06C75")

    def _highlight_json(self, widget):
        txt = self._text_widget(widget)
        self._setup_json_tags(widget)

        for tag in ["json_key", "json_string", "json_number", "json_bool", "json_null"]:
            txt.tag_remove(tag, "1.0", "end")

        content = txt.get("1.0", "end-1c")
        if not content.strip():
            return

        PATTERNS = [
            ("json_key",    r'"[^"]*"(?=\s*:)'),
            ("json_string", r'(?<=:\s)"[^"]*"'),
            ("json_number", r'(?<!["\w])-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\w"])'),
            ("json_bool",   r'\b(?:true|false)\b'),
            ("json_null",   r'\bnull\b'),
        ]

        for tag, raw_pattern in PATTERNS:
            try:
                for m in re.finditer(raw_pattern, content):
                    before = content[:m.start()]
                    row = before.count("\n") + 1
                    col = m.start() - (before.rfind("\n") + 1)
                    end_before = content[:m.end()]
                    end_row = end_before.count("\n") + 1
                    end_col = m.end() - (end_before.rfind("\n") + 1)
                    txt.tag_add(tag, f"{row}.{col}", f"{end_row}.{end_col}")
            except re.PatternError:
                pass