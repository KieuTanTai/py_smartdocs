from shiny import ui


def model_settings_ui(models: list[str]) -> ui.Tag:
    model_choices = models or ["auto"]
    return ui.tags.div(
        ui.tags.div(
            ui.tags.div(
                ui.input_select(
                    "mode_select",
                    "Mode",
                    choices=["normal", "cli-termux"],
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
                    choices=model_choices,
                    selected=model_choices[0],
                ),
                class_="button-select-wrap",
            ),
            class_="select-pill",
        ),
        class_="model-settings",
    )
