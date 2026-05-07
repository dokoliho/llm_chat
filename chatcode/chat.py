from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console

from chatcode.client import make_client, stream_chat
from chatcode.commands import CommandContext, dispatch
from chatcode.models import ChatMessage, ProviderConfig, Session
from chatcode.picker import pick_model_interactive
from chatcode.session import SESSIONS_DIR, load_session, make_session_id, save_session
from chatcode.state import save_last_used

HISTORY_FILE = Path.home() / ".config" / "chatcode" / "history"
console = Console()


def run_chat(
    providers: dict[str, ProviderConfig],
    provider_id: str,
    model_id: str,
    system_prompt: str | None = None,
) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    session = Session(
        id=make_session_id(),
        provider_id=provider_id,
        model_id=model_id,
        system_prompt=system_prompt,
    )
    client = make_client(providers[provider_id])

    prompt_session: PromptSession = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
        multiline=True,
    )

    def _save(filename: str | None) -> None:
        path = save_session(session, filename)
        console.print(f"[green]Session gespeichert:[/green] {path}")

    def _load(filename: str) -> None:
        try:
            loaded = load_session(filename)
            session.messages[:] = loaded.messages
            session.system_prompt = loaded.system_prompt
            nonlocal client
            if loaded.provider_id in providers:
                session.provider_id = loaded.provider_id
                session.model_id = loaded.model_id
                client = make_client(providers[loaded.provider_id])
                ctx.current_provider_id = loaded.provider_id
                ctx.current_model_id = loaded.model_id
            console.print(f"[green]Session geladen:[/green] {len(session.messages)} Nachrichten")
        except FileNotFoundError as exc:
            console.print(f"[red]{exc}[/red]")

    def _pick() -> tuple[str, str]:
        result = pick_model_interactive(providers)
        save_last_used(result[0], result[1])
        return result

    ctx = CommandContext(
        providers=providers,
        messages=session.messages,
        system_prompt=system_prompt,
        current_provider_id=provider_id,
        current_model_id=model_id,
        select_model_interactive=_pick,
        save_session_fn=_save,
        load_session_fn=_load,
    )

    _print_header(providers[provider_id].models[model_id].display_name, provider_id)

    while True:
        try:
            text = prompt_session.prompt("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not text:
            continue

        if text.startswith(":"):
            dispatch(text, ctx)
            if ctx.system_prompt != session.system_prompt:
                session.system_prompt = ctx.system_prompt
            if ctx.current_provider_id != session.provider_id or ctx.current_model_id != session.model_id:
                session.provider_id = ctx.current_provider_id
                session.model_id = ctx.current_model_id
                client = make_client(providers[ctx.current_provider_id])
                save_last_used(ctx.current_provider_id, ctx.current_model_id)
            if ctx.should_exit:
                break
            continue

        user_msg = ChatMessage(role="user", content=text, timestamp=datetime.now())
        session.messages.append(user_msg)

        console.print("[bold dim]Assistant:[/bold dim] ", end="")
        try:
            response_text = stream_chat(
                client,
                session.model_id,
                session.messages,
                session.system_prompt,
                lambda token: console.print(token, end="", highlight=False),
            )
            print()
        except (ConnectionError, RuntimeError, TimeoutError) as exc:
            console.print(f"\n[red bold]Fehler:[/red bold] {exc}")
            session.messages.pop()
            continue

        session.messages.append(
            ChatMessage(role="assistant", content=response_text, timestamp=datetime.now())
        )


def _print_header(display_name: str, provider_id: str) -> None:
    console.print(
        f"[bold green]chatcode[/bold green] — "
        f"[cyan]{display_name}[/cyan] [dim]({provider_id})[/dim]\n"
        f"[dim]Tippe :help für Befehle. Alt+Enter für Zeilenumbruch, Enter zum Senden. Ctrl-C oder :exit zum Beenden.[/dim]\n"
    )
