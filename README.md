# CYPHERpc

**CYPHERpc** = AI mozek + hlas + Vision + Windows assistant + web researcher + coding + gaming + security + monitoring + Control Center + GUI.

Desktopový AI asistent pro Windows na úrovni ChatGPT / Claude – **bez umělých limitů** na délku konverzace, OCR, web výsledky ani API (limit jen pokud si ho sám nastavíš).

## Co umí

- 🧠 **AI Core** – OpenAI, Anthropic, xAI, Google, lokální; auto-výběr modelu; fallback; paměť; osobnost
- 🎤 **Hlas** – wake word **Cypher**, STT/TTS, PTT, výběr mic/hlasu
- 👁️ **Vision** – screenshot, oblast, OCR (plný text), multi-monitor (všechny detekované)
- 🖥️ **Windows** – okna, soubory, clipboard, procesy
- 🎮 **Gaming** – Fortnite kouč (pozice, heal, rotace), auto-detekce her
- 🌐 **Web Agent** – vyhledávání, čtení stránek, citace zdrojů
- 💬 **Chat GUI** – moderní dark UI (CustomTkinter)
- 🎛️ **Control Center** – živý stav CPU/RAM/GPU/AI/Voice/Game
- 🔒 **Privacy + Emergency Stop**
- ⌨️ **Hotkeys** F8–F11, Ctrl+Shift+C/P/X
- 📍 **Tray** (volitelně)
- 🧰 **Tools** – calculator, web, OCR, files, game…
- 🧩 **Plugin API**

## Start

```bash
git clone https://github.com/adamsanchezsh-ui/windows-ai-assistant.git
cd windows-ai-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# vyplň OPENAI_API_KEY / ANTHROPIC_API_KEY / XAI_API_KEY
python -m src.main          # CLI
python -m src.main --gui    # grafické rozhraní
```

## Bez limitů

- Historie konverzace: nastavitelná, výchozí vysoká
- OCR / web fetch: plný obsah (bez zbytečného ořezu)
- API daily limit: `0` = neomezeno
- Monitory: všechny, které OS nahlásí

## Licence

MIT
