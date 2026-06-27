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
