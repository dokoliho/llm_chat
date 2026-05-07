from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from chatcode.config import DEFAULT_CONFIG_PATH, load_config
from chatcode.picker import pick_model_interactive
from chatcode.state import load_last_used, save_last_used

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="chatcode",
        description="Terminal-Chat für OpenAI-kompatible LLMs",
    )
    parser.add_argument("--provider", help="Provider-ID aus opencode.json")
    parser.add_argument("--model", help="Modell-ID")
    parser.add_argument("--config", type=Path, default=None, help="Pfad zur opencode.json")
    parser.add_argument("--system", default=None, help="System-Prompt")
    args = parser.parse_args()

    config_path = args.config or DEFAULT_CONFIG_PATH
    try:
        providers = load_config(config_path)
    except FileNotFoundError as exc:
        console.print(f"[red bold]Fehler:[/red bold] {exc}")
        console.print(f"[dim]Tipp: --config /pfad/zur/opencode.json[/dim]")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"[red bold]Konfigurationsfehler:[/red bold] {exc}")
        sys.exit(1)

    if not providers:
        console.print("[red]Keine Provider in der Konfiguration gefunden.[/red]")
        sys.exit(1)

    provider_id, model_id = _resolve_model(args, providers)

    from chatcode.chat import run_chat
    run_chat(providers, provider_id, model_id, system_prompt=args.system)


def _resolve_model(
    args: argparse.Namespace,
    providers: dict,
) -> tuple[str, str]:
    # CLI flags take priority
    if args.provider and args.model:
        if args.provider not in providers:
            console.print(f"[red]Provider nicht gefunden: {args.provider}[/red]")
            _print_available(providers)
            sys.exit(1)
        if args.model not in providers[args.provider].models:
            console.print(f"[red]Modell nicht gefunden: {args.model}[/red]")
            _print_available(providers)
            sys.exit(1)
        save_last_used(args.provider, args.model)
        return args.provider, args.model

    # Try last-used
    last = load_last_used()
    if last:
        last_prov, last_model = last
        if last_prov in providers and last_model in providers[last_prov].models:
            model = providers[last_prov].models[last_model]
            console.print(
                f"[dim]Letztes Modell:[/dim] [cyan]{model.display_name}[/cyan] "
                f"[dim]({last_prov})[/dim]"
            )
            return last_prov, last_model

    # Interactive selection
    provider_id, model_id = pick_model_interactive(providers)
    save_last_used(provider_id, model_id)
    return provider_id, model_id


def _print_available(providers: dict) -> None:
    console.print("[dim]Verfügbare Provider und Modelle:[/dim]")
    for prov_id, prov in providers.items():
        for model_id in prov.models:
            console.print(f"  [cyan]{prov_id}[/cyan] / {model_id}")
