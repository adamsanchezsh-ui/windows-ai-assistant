"""Wire work services into agent + services dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.work.messaging import MessagingService
from src.work.tasks import TaskManager
from src.work.notes import NotesService
from src.work.reminders import ReminderService
from src.work.email_drafts import EmailDraftService


def create_work_services(data_dir: Path) -> dict[str, Any]:
    msg = MessagingService(data_dir)
    tasks = TaskManager(data_dir)
    notes = NotesService(data_dir)
    reminders = ReminderService(data_dir)
    email = EmailDraftService(data_dir)
    return {
        "work_msg": msg,
        "work_tasks": tasks,
        "work_notes": notes,
        "work_reminders": reminders,
        "work_email": email,
    }


def register_work_tools(agent: Any, services: dict[str, Any]) -> None:
    msg: MessagingService = services["work_msg"]
    tasks: TaskManager = services["work_tasks"]
    notes: NotesService = services["work_notes"]
    reminders: ReminderService = services["work_reminders"]
    email: EmailDraftService = services["work_email"]

    async def list_threads():
        return msg.list_threads()

    async def add_task(title: str, priority: str = "normal"):
        t = tasks.add(title, priority=priority)
        return {"id": t.id, "title": t.title}

    async def list_tasks():
        return [
            {"id": t.id, "title": t.title, "priority": t.priority, "due": t.due}
            for t in tasks.list_open()
        ]

    async def add_note(title: str, body: str):
        n = notes.add(title, body)
        return {"id": n.id, "title": n.title}

    async def list_reminders():
        return [{"id": r.id, "when": r.when, "text": r.text} for r in reminders.list_upcoming()]

    agent.register_tool("list_message_threads", list_threads)
    agent.register_tool("add_task", add_task)
    agent.register_tool("list_tasks", list_tasks)
    agent.register_tool("add_note", add_note)
    agent.register_tool("list_reminders", list_reminders)
