import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    resolved_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(resolved_path, path)

if __name__ == "__main__":
    # In a bundled app, we might need to adjust paths
    # But for now, let's try the standard launch
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--server.headless", "true",
        "--server.port", "8501",
    ]
    sys.exit(stcli.main())
