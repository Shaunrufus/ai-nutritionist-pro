"""
Streamlit Cloud root entrypoint redirect.
Executes app/Streamlit_app.py with all resilient fallback systems.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

app_path = root_dir / "app" / "Streamlit_app.py"
with open(app_path, "r", encoding="utf-8") as f:
    code = compile(f.read(), str(app_path), "exec")
    exec(code, globals())
