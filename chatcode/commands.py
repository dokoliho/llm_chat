from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from chatcode.models import ChatMessage, ProviderConfig


@dataclass
class CommandContext:
    providers: dict[str, ProviderConfig]
    messages: list[ChatMessage]
    system_prompt: str | None
    current_provider_id: str
    current_model_id: str
    should_exit: bool = False
    select_model_interactive: Callable[[], tuple[str, str]] | None = None
    save_session_fn: Callable[[str | None], None] | None = None
    load_session_fn: Callable[[str], None] | None = None


HELP_TEXT = """\
[bold]Verfügbare Befehle:[/bold]
  [cyan]:help[/cyan]                   Zeigt diese Hilfe
  [cyan]:models[/cyan]                 Listet alle Provider und Modelle
  [cyan]:use [provider model][/cyan]   Modell wechseln (ohne Args: interaktive Auswahl)
  [cyan]:clear[/cyan]                  Chatverlauf löschen (System-Prompt bleibt)
  [cyan]:system [text][/cyan]          System-Prompt setzen/anzeigen (ohne Args: anzeigen)
  [cyan]:info[/cyan]                   Aktiver Provider, Modell, baseURL
  [cyan]:save [dateiname][/cyan]       Session speichern
  [cyan]:load <dateiname>[/cyan]       Session laden
  [cyan]:exit[/cyan]                   Beenden
"""


def parse_command(text: str) -> tuple[str, list[str]]:
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower()
    args_str = parts[1] if len(parts) > 1 else ""
    args = args_str.split(None, 1) if args_str else []
    return cmd, args


def dispatch(text: str, context: CommandContext) -> None:
    cmd, args = parse_command(text)
    handlers: dict[str, Callable] = {
        ":help": _cmd_help,
        ":models": _cmd_models,
        ":use": _cmd_use,
        ":clear": _cmd_clear,
        ":system": _cmd_system,
        ":info": _cmd_info,
        ":save": _cmd_save,
        ":load": _cmd_load,
        ":exit": _cmd_exit,
    }
    handler = handlers.get(cmd)
    if handler is None:
        Console().print(f"[yellow]Unbekannter Befehl: {cmd}[/yellow] — [dim]:help für Hilfe[/dim]")
        return
    handler(args, context)


def _cmd_help(args: list[str], ctx: CommandContext) -> None:
    Console().print(HELP_TEXT)


def _cmd_models(args: list[str], ctx: CommandContext) -> None:
    console = Console()
    for prov_id, prov in ctx.providers.items():
        table = Table(title=f"[bold]{prov_id}[/bold]  [dim]{prov.base_url}[/dim]")
        table.add_column("Modell-ID", style="cyan")
        table.add_column("Anzeigename")
        for model_id, model in prov.models.items():
            table.add_row(model_id, model.display_name)
        console.print(table)


def _cmd_use(args: list[str], ctx: CommandContext) -> None:
    if len(args) >= 2:
        provider_id, model_id = args[0], args[1]
        if provider_id not in ctx.providers:
            Console().print(f"[red]Provider nicht gefunden: {provider_id}[/red]")
            return
        if model_id not in ctx.providers[provider_id].models:
            Console().print(f"[red]Modell nicht gefunden: {model_id}[/red]")
            return
        ctx.current_provider_id = provider_id
        ctx.current_model_id = model_id
        model = ctx.providers[provider_id].models[model_id]
        Console().print(f"[green]Gewechselt zu:[/green] {provider_id} / {model.display_name}")
    elif ctx.select_model_interactive:
        provider_id, model_id = ctx.select_model_interactive()
        ctx.current_provider_id = provider_id
        ctx.current_model_id = model_id
        model = ctx.providers[provider_id].models[model_id]
        Console().print(f"[green]Gewechselt zu:[/green] {provider_id} / {model.display_name}")


def _cmd_clear(args: list[str], ctx: CommandContext) -> None:
    ctx.messages.clear()
    Console().print("[dim]Chatverlauf gelöscht.[/dim]")


def _cmd_system(args: list[str], ctx: CommandContext) -> None:
    console = Console()
    if args:
        text = " ".join(args)
        ctx.system_prompt = text
        console.print(f"[green]System-Prompt gesetzt:[/green] {text}")
    else:
        if ctx.system_prompt:
            console.print(f"[dim]System-Prompt:[/dim] {ctx.system_prompt}")
        else:
            console.print("[dim]Kein System-Prompt gesetzt.[/dim]")


def _cmd_info(args: list[str], ctx: CommandContext) -> None:
    console = Console()
    prov = ctx.providers.get(ctx.current_provider_id)
    model = prov.models.get(ctx.current_model_id) if prov else None
    console.print(f"[bold]Provider:[/bold]  {ctx.current_provider_id}")
    console.print(f"[bold]Modell:[/bold]    {ctx.current_model_id}")
    if model:
        console.print(f"[bold]Anzeige:[/bold]   {model.display_name}")
    if prov:
        console.print(f"[bold]baseURL:[/bold]   {prov.base_url}")
    if ctx.system_prompt:
        console.print(f"[bold]System:[/bold]    {ctx.system_prompt}")


def _cmd_save(args: list[str], ctx: CommandContext) -> None:
    if ctx.save_session_fn:
        filename = args[0] if args else None
        ctx.save_session_fn(filename)


def _cmd_load(args: list[str], ctx: CommandContext) -> None:
    if not args:
        Console().print("[red]:load erwartet einen Dateinamen.[/red]")
        return
    if ctx.load_session_fn:
        ctx.load_session_fn(args[0])


def _cmd_exit(args: list[str], ctx: CommandContext) -> None:
    ctx.should_exit = True
