"""CYPHERpc modern Chat + Control Center GUI (CustomTkinter)."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

try:
    import customtkinter as ctk
except ImportError:
    ctk = None  # type: ignore


class CypherGUI:
    """
    Modern dark chat UI + side panel Control Center.
    Requires: pip install customtkinter
    """

    def __init__(
        self,
        on_send: Callable[[str], Awaitable[str]] | None = None,
        get_status: Callable[[], dict[str, Any]] | None = None,
        on_privacy: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        title: str = "CYPHERpc",
    ):
        if ctk is None:
            raise RuntimeError("customtkinter not installed")
        self.on_send = on_send
        self.get_status = get_status
        self.on_privacy = on_privacy
        self.on_stop = on_stop
        self._loop: asyncio.AbstractEventLoop | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title(title)
        self.root.geometry("1100x700")
        self.root.minsize(800, 500)

        self._build()

    def _build(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Sidebar – Control Center
        side = ctk.CTkFrame(self.root, width=260, corner_radius=0)
        side.grid(row=0, column=0, rowspan=2, sticky="nsew")
        side.grid_propagate(False)

        ctk.CTkLabel(side, text="CYPHERpc", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(side, text="Control Center", text_color="gray").pack(pady=(0, 15))

        self.status_box = ctk.CTkTextbox(side, height=320, width=240, font=ctk.CTkFont(family="Consolas", size=12))
        self.status_box.pack(padx=10, pady=5)
        self.status_box.insert("1.0", "Načítám stav…")
        self.status_box.configure(state="disabled")

        ctk.CTkButton(side, text="Obnovit stav", command=self.refresh_status).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(side, text="Privacy Mode", fg_color="#6B21A8", command=self._privacy).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(side, text="Emergency Stop", fg_color="#B91C1C", command=self._stop).pack(padx=10, pady=5, fill="x")

        # Chat area
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_box = ctk.CTkTextbox(chat_frame, font=ctk.CTkFont(size=14), wrap="word")
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_box.insert("end", "CYPHERpc připraven. Piš česky nebo anglicky…\n\n")
        self.chat_box.configure(state="disabled")

        # Input
        input_frame = ctk.CTkFrame(self.root)
        input_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Zpráva pro CYPHERpc…", height=40)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(5, 5), pady=5)
        self.entry.bind("<Return>", lambda e: self._on_send())

        self.send_btn = ctk.CTkButton(input_frame, text="Odeslat", width=100, command=self._on_send)
        self.send_btn.grid(row=0, column=1, padx=5, pady=5)

        self.refresh_status()

    def _append(self, role: str, text: str) -> None:
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{role}: {text}\n\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _on_send(self) -> None:
        text = self.entry.get().strip()
        if not text or not self.on_send:
            return
        self.entry.delete(0, "end")
        self._append("Ty", text)
        self.send_btn.configure(state="disabled")

        def worker():
            try:
                loop = asyncio.new_event_loop()
                reply = loop.run_until_complete(self.on_send(text))
                loop.close()
                self.root.after(0, lambda: self._append("CYPHERpc", reply))
            except Exception as e:
                self.root.after(0, lambda: self._append("Chyba", str(e)))
            finally:
                self.root.after(0, lambda: self.send_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_status(self) -> None:
        if not self.get_status:
            return
        try:
            st = self.get_status()
            lines = [f"{k}: {v}" for k, v in st.items()]
            self.status_box.configure(state="normal")
            self.status_box.delete("1.0", "end")
            self.status_box.insert("1.0", "\n".join(lines))
            self.status_box.configure(state="disabled")
        except Exception as e:
            logger.exception("status refresh: %s", e)

    def _privacy(self) -> None:
        if self.on_privacy:
            self.on_privacy()
            self.refresh_status()

    def _stop(self) -> None:
        if self.on_stop:
            self.on_stop()
            self.refresh_status()

    def run(self) -> None:
        self.root.mainloop()

    def destroy(self) -> None:
        self.root.destroy()
