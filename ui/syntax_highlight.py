import re


# ── Paleta de cores por tema ───────────────────────────────────────────────
HIGHLIGHT_DARK = {
    "json_key":     "#79c0ff",  # azul claro
    "json_string":  "#a5d6a7",  # verde
    "json_number":  "#f78c6c",  # laranja
    "json_bool":    "#c792ea",  # roxo
    "json_null":    "#c792ea",  # roxo
    "json_bracket": "#89ddff",  # ciano

    "py_keyword":   "#c792ea",  # roxo
    "py_builtin":   "#82aaff",  # azul
    "py_string":    "#a5d6a7",  # verde
    "py_comment":   "#546e7a",  # cinza
    "py_number":    "#f78c6c",  # laranja
    "py_selfcls":   "#f07178",  # rosa
    "py_decorator": "#ffcb6b",  # amarelo
}

HIGHLIGHT_LIGHT = {
    "json_key":     "#0550ae",
    "json_string":  "#116329",
    "json_number":  "#953800",
    "json_bool":    "#8250df",
    "json_null":    "#8250df",
    "json_bracket": "#0969da",

    "py_keyword":   "#8250df",
    "py_builtin":   "#0550ae",
    "py_string":    "#116329",
    "py_comment":   "#6e7781",
    "py_number":    "#953800",
    "py_selfcls":   "#cf222e",
    "py_decorator": "#953800",
}


# ── Regras JSON ────────────────────────────────────────────────────────────
JSON_RULES = [
    ("json_key",     r'"([^"\$$||\\.)*"\s*(?=:)'),
    ("json_string",  r'"([^"\$$||\\.)*"'),
    ("json_number",  r'-?\b\d+(\.\d+)?([eE][+-]?\d+)?\b'),
    ("json_bool",    r'\b(true|false)\b'),
    ("json_null",    r'\bnull\b'),
    ("json_bracket", r'[{}|$$$$|,:]'),
]

# ── Regras Python ──────────────────────────────────────────────────────────
PY_KEYWORDS = (
    r'\b(False|None|True|and|as|assert|async|await|break|class|continue|'
    r'def|del|elif|else|except|finally|for|from|global|if|import|in|is|'
    r'lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b'
)

PY_BUILTINS = (
    r'\b(print|len|range|str|int|float|list|dict|tuple|set|bool|type|'
    r'isinstance|hasattr|getattr|setattr|open|json|request|response|env)\b'
)

PY_RULES = [
    ("py_comment",   r'#[^\n]*'),
    ("py_string",    r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\n\$$|*(?:\\.[^"\n\$$|*)*"|\'[^\'\n\$$|*(?:\\.[^\'\n\$$|*)*\''),
    ("py_decorator", r'@\w+'),
    ("py_keyword",   PY_KEYWORDS),
    ("py_builtin",   PY_BUILTINS),
    ("py_selfcls",   r'\b(self|cls)\b'),
    ("py_number",    r'\b\d+(\.\d+)?\b'),
]


def _apply_highlights(textbox, rules: list, palette: dict):
    """Aplica highlight em um CTkTextbox usando tags do Tkinter."""
    widget = textbox._textbox  # acessa o widget tk interno

    # Remove tags antigas
    for tag, _ in rules:
        widget.tag_remove(tag, "1.0", "end")
        widget.tag_configure(tag, foreground=palette[tag])

    content = widget.get("1.0", "end-1c")

    for tag, pattern in rules:
        for match in re.finditer(pattern, content, re.MULTILINE):
            start, end = match.start(), match.end()
            line_start = content.rfind("\n", 0, start) + 1
            start_line = content[:start].count("\n") + 1
            start_col  = start - line_start
            end_line   = content[:end].count("\n") + 1
            end_col    = end - (content.rfind("\n", 0, end) + 1)
            widget.tag_add(
                tag,
                f"{start_line}.{start_col}",
                f"{end_line}.{end_col}"
            )


def highlight_json(textbox, dark_mode: bool = True):
    palette = HIGHLIGHT_DARK if dark_mode else HIGHLIGHT_LIGHT
    _apply_highlights(textbox, JSON_RULES, palette)


def highlight_python(textbox, dark_mode: bool = True):
    palette = HIGHLIGHT_DARK if dark_mode else HIGHLIGHT_LIGHT
    _apply_highlights(textbox, PY_RULES, palette)