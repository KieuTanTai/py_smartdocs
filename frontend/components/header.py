from shiny import ui


def header_ui(
    api_base_url: str,
    provider: str,
    system_prompt: str,
    mock_on_fail: bool,
) -> ui.Tag:
    return ui.tags.header(
        ui.tags.div(
            ui.tags.img(src="analysis.png", class_="logo"),
            ui.tags.div(
                ui.tags.div("SmartDocs", class_="brand-title"),
                ui.tags.div("Document intelligence studio", class_="brand-sub"),
                class_="brand-text",
            ),
            class_="brand",
        ),
        ui.tags.div(
            ui.output_ui("model_badge"),
            class_="header-badges",
        ),
        ui.tags.div(
            settings_button_ui(),
            class_="header-actions",
        ),
        class_="app-header",
    )


def settings_button_ui() -> ui.Tag:
    return ui.input_action_button(
        "open_settings",
        ui.tags.img(src="settings.png", class_="icon"),
        class_="icon-btn",
    )


