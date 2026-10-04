"""CLI handlers for work features: messages, tasks, notes, reminders, email drafts."""

from __future__ import annotations

from typing import Any

from src.work.messaging import MessagingService
from src.work.tasks import TaskManager
from src.work.notes import NotesService
from src.work.reminders import ReminderService
from src.work.email_drafts import EmailDraftService


HELP = """
Pracovní příkazy:
  /msg threads              seznam konverzací
  /msg new <název>          nové vlákno
  /msg add <tid> <text>     přidej příchozí zprávu
  /msg show <tid>           zobraz zprávy
  /msg summary <tid>        AI shrnutí (přes chat)
  /msg reply <tid>          AI návrh odpovědi (neodesílá)

  /todo                     otevřené úkoly
  /todo add <text>          nový úkol
  /todo done <id>           hotovo
  /todo del <id>            smazat
  /todo plan                AI prioritizace

  /note                     seznam poznámek
  /note add <titulek> | <text>
  /note search <dotaz>
  /note meeting <text>      uspořádej zápis z meetingu (AI)

  /remind                   připomínky
  /remind add <kdy ISO> <text>
  /remind due               splatné teď

  /email                    drafty e-mailů
  /email draft <komu> | <záměr>   AI napíše draft (neodesílá)
  /email list
"""


async def handle_work_command(
    user: str,
    *,
    msg: MessagingService,
    tasks: TaskManager,
    notes: NotesService,
    reminders: ReminderService,
    email: EmailDraftService,
    agent: Any = None,
) -> bool:
    """Return True if command was handled."""
    low = user.lower().strip()
    parts = user.split(maxsplit=3)

    if low in ("/work", "/work help"):
        print(HELP)
        return True

    # --- Messages ---
    if low == "/msg threads" or low == "/msg":
        threads = msg.list_threads()
        if not threads:
            print("(žádná vlákna – /msg new Název)")
        for t in threads:
            print(f"  [{t['id']}] {t['title']} ({t['messages']}) {t['last'][:50]}")
        return True

    if low.startswith("/msg new "):
        title = user[len("/msg new "):].strip()
        t = msg.create_thread(title)
        print(f"Vlákno: {t.id} — {t.title}")
        return True

    if low.startswith("/msg add "):
        # /msg add <tid> <text>
        rest = user[len("/msg add "):].strip()
        sp = rest.split(maxsplit=1)
        if len(sp) < 2:
            print("Použití: /msg add <thread_id> <text>")
            return True
        tid, text = sp[0], sp[1]
        m = msg.add_message(tid, sender="contact", text=text, direction="in")
        print(f"+ [{m.id}] {m.text[:80]}")
        return True

    if low.startswith("/msg show "):
        tid = user.split(maxsplit=2)[2] if len(user.split()) > 2 else ""
        for m in msg.get_messages(tid):
            arrow = "←" if m.direction == "in" else "→"
            print(f"  {arrow} {m.sender}: {m.text}")
        return True

    if low.startswith("/msg summary ") and agent:
        tid = user.split(maxsplit=2)[2]
        prompt = msg.summary_prompt(tid)
        print(await agent.chat(prompt))
        return True

    if low.startswith("/msg reply ") and agent:
        tid = user.split(maxsplit=2)[2]
        prompt = msg.reply_prompt(tid)
        suggestion = await agent.chat(prompt)
        print("Návrh odpovědi (NEODESLÁNO):\n", suggestion)
        print(msg.draft_reply(tid, suggestion))
        return True

    # --- Tasks ---
    if low == "/todo":
        open_t = tasks.list_open()
        if not open_t:
            print("(žádné úkoly)")
        for t in open_t:
            due = f" do {t.due}" if t.due else ""
            print(f"  [{t.id}] ({t.priority}) {t.title}{due}")
        return True

    if low.startswith("/todo add "):
        title = user[len("/todo add "):].strip()
        t = tasks.add(title)
        print(f"+Úkol [{t.id}] {t.title}")
        return True

    if low.startswith("/todo done "):
        tid = user.split()[2] if len(user.split()) > 2 else ""
        print("OK" if tasks.complete(tid) else "Nenalezeno")
        return True

    if low.startswith("/todo del "):
        tid = user.split()[2] if len(user.split()) > 2 else ""
        print("Smazáno" if tasks.delete(tid) else "Nenalezeno")
        return True

    if low == "/todo plan" and agent:
        print(await agent.chat(tasks.summary_prompt()))
        return True

    # --- Notes ---
    if low == "/note":
        for n in notes.list_all()[:30]:
            print(f"  [{n.id}] ({n.kind}) {n.title}")
        return True

    if low.startswith("/note add "):
        rest = user[len("/note add "):]
        if "|" in rest:
            title, body = rest.split("|", 1)
        else:
            title, body = rest[:40], rest
        n = notes.add(title.strip(), body.strip())
        print(f"Poznámka [{n.id}] {n.title}")
        return True

    if low.startswith("/note search "):
        q = user[len("/note search "):].strip()
        for n in notes.search(q):
            print(f"  [{n.id}] {n.title}")
        return True

    if low.startswith("/note meeting ") and agent:
        raw = user[len("/note meeting "):]
        result = await agent.chat(notes.meeting_prompt(raw))
        print(result)
        notes.add("Meeting notes", result, kind="meeting")
        print("(uloženo jako meeting note)")
        return True

    # --- Reminders ---
    if low == "/remind":
        for r in reminders.list_upcoming():
            print(f"  [{r.id}] {r.when} — {r.text}")
        return True

    if low.startswith("/remind add "):
        rest = user[len("/remind add "):].strip()
        sp = rest.split(maxsplit=1)
        if len(sp) < 2:
            print("Použití: /remind add 2026-10-05T15:00:00Z Zavolat klientovi")
            return True
        when, text = sp[0], sp[1]
        r = reminders.add(text, when)
        print(f"Připomínka [{r.id}] {r.when}: {r.text}")
        return True

    if low == "/remind due":
        due = reminders.due_now()
        if not due:
            print("(nic splatného)")
        for r in due:
            print(f"  ⏰ [{r.id}] {r.text}")
        return True

    # --- Email ---
    if low == "/email" or low == "/email list":
        for d in email.list_drafts():
            print(f"  [{d.id}] To: {d.to} | {d.subject}")
        return True

    if low.startswith("/email draft ") and agent:
        rest = user[len("/email draft "):]
        if "|" not in rest:
            print("Použití: /email draft email@x.com | Prosím o termín schůzky")
            return True
        to, intent = rest.split("|", 1)
        draft_text = await agent.chat(email.compose_prompt(to.strip(), intent.strip()))
        print(draft_text)
        # naive split subject/body
        lines = draft_text.strip().split("\n")
        subject = lines[0][:120] if lines else intent.strip()[:60]
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else draft_text
        d = email.create(to=to.strip(), subject=subject, body=body)
        print(f"\nDraft uložen [{d.id}] — NENÍ odeslán.")
        return True

    return False
