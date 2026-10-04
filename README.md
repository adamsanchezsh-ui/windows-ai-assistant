# CYPHERpc

Desktopový AI asistent pro Windows – chat, hlas (Grok-like), work tools, Fortnite, privacy.

**Demo režim** funguje bez API klíče. S klíčem = plné AI.

---

## CYPHERpc.exe (Windows)

Na **tvém PC** sestav exe:

```powershell
git clone https://github.com/adamsanchezsh-ui/windows-ai-assistant.git
cd windows-ai-assistant
.\scripts\build_exe.ps1
```

Výsledek: `dist\CYPHERpc.exe`

1. Vedle exe měj `.env` (zkopíruj z `.env.example`)
2. Volitelně API klíč v `.env`
3. Dvojklik **CYPHERpc.exe**
4. GUI: `CYPHERpc.exe --gui`

Exe se na GitHub **nenahrává** (je velký) – build u tebe trvá cca 1–3 min.

---

## Python (bez exe)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python scripts\smoke_test.py
python -m src.main
```

---

## API

```env
OPENAI_API_KEY=sk-...
PRIMARY_MODEL=openai:gpt-4o-mini
```

## Příkazy

`/help` `/settings` `/voice` `/persona` `/work` `/todo` `/fortnite` `/cc`

Více: [START_HERE.md](START_HERE.md)

MIT
