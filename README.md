# CYPHERpc

**CYPHERpc** = AI mozek + hlasový asistent + Vision + Windows assistant + web researcher + coding assistant + gaming assistant + security center + PC monitoring + automatizace + Control Center.

Moderní desktopový AI asistent pro Windows – chytrý jako ChatGPT / Claude, ale ovládá tvůj PC.

## Hlavní pilíře

| Modul | Co dělá |
|-------|--------|
| 🧠 **AI Core** | Více providerů, auto-výběr modelu, fallback, reasoning/coding/creative/research, paměť, osobnost |
| 🎤 **Hlas** | Wake word **„Cypher“**, STT/TTS, čeština+, push-to-talk, výběr mikrofonu/hlasu |
| 👁️ **Vision** | Screenshoty, OCR, UI analýza, multi-monitor, oblast, on-demand/periodic |
| 🖥️ **Windows Assistant** | Aplikace, okna, soubory, clipboard, procesy, notifikace |
| 🎮 **Gaming** | Profily, overlay, rady (Fortnite…), priority, auto-detekce hry |
| ⚡ **Performance** | CPU/RAM/GPU/disk/síť, Quality/Balanced/Performance |
| 🛡️ **Security Center** | Podezřelé soubory/procesy, Defender, karanténa, audit log |
| 📁 **File AI** | Hledání, třídění, sumarizace, bezpečné mazání |
| 🌐 **Web Agent** | Vyhledávání, shrnutí, citace zdrojů, Research Mode |
| 💬 **Chat** | Moderní UI, historie, přílohy, regenerace, export |
| 🧰 **AI Tools** | Calculator, Python, web, OCR, vision, files, game… |
| 🔐 **Permissions** | READ_SCREEN, DELETE_FILE… + potvrzení |
| 🎛️ **Control Center** | CYPHERpc ONLINE, AI, MODEL, VOICE, VISION, GAME, CPU… |
| 🧩 **Plugins** | Modulární API (Spotify, Discord, Browser…) |
| 🔔 **Smart Notifications** | Shrnutí, DND, Gaming/School/Work režim |
| 📚 **School Mode** | Výuka, obtížnost, práce s obrázkem zadání |
| 🌙 **Profiles** | Gaming / School / Privacy / Work |
| 🔒 **Privacy Center** | Co běží + one-click kill switch |

## Rychlý start

```bash
git clone https://github.com/adamsanchezsh-ui/windows-ai-assistant.git
cd windows-ai-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # vyplň API klíče
python -m src.main
```

## Wake word

Řekni **„Cypher“** (nebo stiskni push-to-talk) → AI naslouchá příkazu.

## Bezpečnost

- Žádný cheating / anti-cheat bypass
- Rizikové akce = potvrzení
- Privacy Mode / Emergency Stop okamžitě vše vypne
- Secrets jen v `.env`

## Licence

MIT
