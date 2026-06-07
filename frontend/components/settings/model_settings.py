from shiny import ui
from sys_services.read_config.read_list_provider import LIST_PROVIDERS


def model_settings_ui(models: list[str]) -> ui.Tag:
    # Build choices from LIST_PROVIDERS for the model select dropdown
    model_choices: list[str] = []
    for p in LIST_PROVIDERS:
        model_choices.append(p.model_name)

    mode_choices = ["normal", "graph rag"]

    return ui.tags.div(
        ui.tags.div(
            ui.tags.div(
                ui.input_select(
                    "mode_select",
                    "Mode",
                    choices={c: c for c in mode_choices},
                    selected="normal",
                ),
                class_="button-select-wrap",
            ),
            class_="select-pill",
        ),
        ui.tags.div(
            ui.tags.div(
                ui.input_select(
                    "model_select",
                    "Model",
                    choices={c: c for c in model_choices},
                    selected=model_choices[0] if model_choices else "auto",
                ),
                class_="button-select-wrap",
            ),
            class_="select-pill",
        ),
        class_="model-settings",
    )
