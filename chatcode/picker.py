from __future__ import annotations

from prompt_toolkit.shortcuts import radiolist_dialog

from chatcode.models import ProviderConfig


def pick_model_interactive(providers: dict[str, ProviderConfig]) -> tuple[str, str]:
    """Show an arrow-key selection dialog. Returns (provider_id, model_id).
    Raises SystemExit if the user cancels."""
    values: list[tuple[tuple[str, str], str]] = []
    for prov_id, prov in providers.items():
        for model_id, model in prov.models.items():
            label = f"{prov_id}  /  {model.display_name}"
            values.append(((prov_id, model_id), label))

    if not values:
        raise RuntimeError("Keine Modelle in der Konfiguration gefunden.")

    result = radiolist_dialog(
        title="chatcode — Modell auswählen",
        text="Pfeiltasten zum Navigieren, Enter zum Bestätigen, Ctrl-C zum Abbrechen:",
        values=values,
    ).run()

    if result is None:
        raise SystemExit(0)

    return result
