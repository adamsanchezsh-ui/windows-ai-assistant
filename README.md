# CYPHERpc

Desktopový AI asistent pro Windows – chat (Grok/ChatGPT úroveň), hlas, work tools, Fortnite kouč, vision, privacy.

**Použitelné hned** – i bez API klíče běží **demo režim** (příkazy, úkoly, herní tipy). S klíčem máš plné AI.

---

## Rychlý start (Windows)

```powershell
git clone https://github.com/adamsanchezsh-ui/windows-ai-assistant.git
cd windows-ai-assistant

# A) setup skript
.\scripts\setup.ps1

# NEBO ručně:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### Test že to žije

```powershell
python scripts\smoke_test.py
python -m src.main
```

V chatu zkus:

```text
ahoj
/todo add Otestovat CYPHERpc
/todo
/settings
/persona
/fortnite
/heal 35
/cc
/help
```

GUI: `python -m src.main --gui`  nebo  `.\scripts\run_gui.bat`

---

## API klíč (plné AI)

Uprav `.env` – stačí **jeden**:

```env
OPENAI_API_KEY=sk-...
# nebo
XAI_API_KEY=xai-...
# nebo
ANTHROPIC_API_KEY=sk-ant-...

PRIMARY_MODEL=openai:gpt-4o
# pro xAI:
# PRIMARY_MODEL=xai:grok-2-latest
```

Bez klíče = automaticky **demo** provider (stále můžeš testovat vše kromě ostrého LLM).

---

## Hlavní příkazy

| Příkaz | Popis |
|--------|--------|
| `/settings` | styl odpovědí jako Grok |
| `/voice` `/persona` `/wake` | hlas + Grok persony |
| `/work` `/todo` `/note` `/email` | práce |
| `/fortnite` `/heal` `/pos` `/rotate` | herní kouč |
| `/search ...` | web |
| `/cc` | Control Center |
| `/privacy` `/stop` | soukromí / emergency |

---

## Co umí

- AI Core (OpenAI, Anthropic, xAI, local, **demo**)
- Grok-like hlasy (edge-tts)
- Work suite (zprávy, úkoly, poznámky, e-mail drafty)
- Fortnite guidance, Windows tools, web, privacy
- CLI + GUI

---

## Licence

MIT
