# CYPHERpc

AI asistent pro Windows – chat, hlas, work, Fortnite, privacy.

## Jednim prikazem (stahne i Python)

```powershell
git clone https://github.com/adamsanchezsh-ui/windows-ai-assistant.git
cd windows-ai-assistant
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\full_setup.ps1 -BuildExe
```

- Stahne **portable Python 3.12**, pokud ho nemas
- Nainstaluje zavislosti + smoke test
- Sestavi **`dist\CYPHERpc.exe`**

Pak spust `dist\CYPHERpc.exe` (vedle nej `.env`).

Jen setup bez exe:

```powershell
.\scripts\full_setup.ps1
```

Jen Python:

```powershell
.\scripts\download_python.ps1
```

## API (volitelne)

V `.env`:

```env
OPENAI_API_KEY=sk-...
PRIMARY_MODEL=openai:gpt-4o-mini
```

Bez klice = demo rezim.

## Prikazy

`/help` `/settings` `/voice` `/persona` `/todo` `/fortnite` `/cc`

[START_HERE.md](START_HERE.md)

MIT
