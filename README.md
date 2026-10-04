# Windows AI Assistant

Pokročilý modulární AI desktop asistent pro Windows PC.

## Funkce (základ)

- **Univerzální AI asistent** – konverzace, reasoning, coding, research, school, creative
- **Model Router** – OpenAI, Anthropic, xAI, Google, lokální / OpenAI-compatible API + fallback
- **Desktop Control** – klávesnice, myš, okna, aplikace, soubory (s potvrzením rizikových akcí)
- **AI Vision** – screenshoty, OCR, analýza UI, režimy OFF / ON DEMAND / PERIODIC
- **Herní AI** – profily pro Minecraft, Fortnite, CS2, Valorant, LoL, ... (pouze poradenské funkce, žádný cheating)
- **Overlay** – always-on-top rady a stav
- **Performance Manager** – Quality / Balanced / Performance + priorita procesu
- **Hlasový asistent** – čeština + další jazyky, hotkeys F8/F9/F10
- **PC Monitoring Dashboard**
- **Správa souborů, Smart Clipboard, Browser Assistant, Messaging**
- **Bezpečnost** – malware checks, karanténa, potvrzení
- **School Mode, Privacy Mode, App/Game Profiles**
- **Tool system + permissions**
- **Lokální auth + session management**

## Architektura

```
src/
  agent.py          # Hlavní AI agent + tool orchestrace
  model.py          # Model router + providers
  desktop.py        # Ovládání PC
  screen.py         # Vision / screenshots / OCR
  voice.py          # TTS / STT
  overlay.py        # Always-on-top overlay
  settings.py       # Konfigurace
  game_profiles.py  # Herní profily
  game_adapters.py  # Adaptéry pro hry
  priority.py       # Priorita procesů
  priority_monitor.py
  performance.py
  security.py
  files.py
  clipboard.py
  browser.py
  messaging.py
  monitoring.py
  auth.py
  tools/            # Tool implementace
  ui/               # Control Center + Chat UI
  main.py
config/
tests/
.env.example
requirements.txt
```

## Rychlý start

1. Naklonuj repozitář
2. Vytvoř virtuální prostředí a nainstaluj závislosti:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Zkopíruj `.env.example` → `.env` a vyplň API klíče
4. Spusť:
   ```bash
   python -m src.main
   ```

## Bezpečnostní pravidla

- Žádné obcházení anti-cheatu
- Žádné automatické mazání důležitých souborů
- Rizikové akce vyžadují potvrzení uživatele
- Secrets pouze v `.env` / secrets manageru
- Privacy Mode okamžitě zastaví vision, voice listening a automatické skeny

## Licence

MIT (nebo dle volby majitele)

---

Toto je **dobře strukturovaný základ** pro skutečný Windows AI asistent, který lze postupně rozšiřovat.
