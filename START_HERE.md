# START HERE – otestuj CYPHERpc za 3 minuty

## 1. Instalace

```powershell
cd windows-ai-assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## 2. Smoke test

```powershell
python scripts\smoke_test.py
```

Musí vypsat samá `OK`.

## 3. Spusť

```powershell
python -m src.main
```

Napiš `ahoj` – odpoví i **bez API klíče** (demo).

Zkuste:
- `/todo add Test`
- `/todo`
- `/persona`
- `/fortnite`
- `/heal 40`
- `/cc`
- `/quit`

## 4. Ostré AI (volitelné)

Do `.env`:

```
OPENAI_API_KEY=sk-tvuj-klic
PRIMARY_MODEL=openai:gpt-4o-mini
```

Restart `python -m src.main` – už odpovídá opravdový model.

## 5. Hlas (volitelné)

```
/voice
/persona grok_cs
/speak test
```

(potřeba `edge-tts` – je v requirements)

---

Hotovo. Repo: https://github.com/adamsanchezsh-ui/windows-ai-assistant
