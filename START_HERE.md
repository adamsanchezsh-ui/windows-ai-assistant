# START HERE – CYPHERpc na Windows

## Varianta A: Vse automaticky (doporuceno)

V PowerShellu ve slozce projektu:

```powershell
# Pokud PowerShell blokuje skripty:
Set-ExecutionPolicy -Scope Process Bypass

# Stahne Python (kdyz neni), nainstaluje balicky, otestuje
.\scripts\full_setup.ps1

# + sestavi CYPHERpc.exe
.\scripts\full_setup.ps1 -BuildExe
```

Pak:

```text
dist\CYPHERpc.exe
```

Vedle exe bude `.env` – volitelne dopln `OPENAI_API_KEY`.

## Varianta B: Uz mas Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python scripts\smoke_test.py
python -m src.main
```

## Varianta C: Jen stahnout Python

```powershell
.\scripts\download_python.ps1
```

Portable Python bude ve slozce `python\`.

---

## Po instalaci

```text
ahoj
/todo add Test
/persona
/fortnite
/heal 40
/cc
/quit
```

Plne AI: do `.env` dej napr. `OPENAI_API_KEY=sk-...` a restart.

Repo: https://github.com/adamsanchezsh-ui/windows-ai-assistant
