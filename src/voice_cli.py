"""CLI helpers for Grok-like voice personas."""

from __future__ import annotations

from src.voice import GROK_VOICES, VoiceService, list_grok_personas


async def handle_voice_command(user: str, voice: VoiceService) -> bool:
    low = user.lower().strip()

    if low == "/voice":
        on = voice.toggle()
        print(f"Voice: {'ON' if on else 'OFF'} | persona: {voice.current_persona().label}")
        return True

    if low == "/wake":
        on = voice.toggle_wake_word()
        print(f"Wake word 'Cypher': {'ON' if on else 'OFF'}")
        return True

    if low == "/persona" or low == "/voices":
        print("Grok-like hlasy:")
        for p in list_grok_personas():
            mark = " *" if p.key == voice.persona_key else ""
            print(f"  {p.key}: {p.label}{mark}")
        print("Použití: /persona grok_cs")
        return True

    if low.startswith("/persona "):
        key = user.split(maxsplit=1)[1].strip()
        print(voice.set_persona(key))
        return True

    if low == "/speak test":
        await voice.speak(
            "Ahoj, jsem CYPHERpc. Mluvím přímo a s nadhledem — ve stylu Grok."
        )
        return True

    return False
