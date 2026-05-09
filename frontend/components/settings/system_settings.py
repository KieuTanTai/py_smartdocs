from shiny import ui


def system_settings_modal(
    api_base_url: str,
    provider: str,
    system_prompt: str,
    mock_on_fail: bool,
) -> ui.Tag:
    return ui.modal(
        ui.tags.div(
            ui.input_text("api_base_url", "API base URL", value=api_base_url),
            ui.input_select(
                "provider_select",
                "Provider",
                choices=["auto", "gemini", "ollama"],
                selected=provider,
            ),
            ui.input_text(
                "system_prompt",
                "System prompt",
                value=system_prompt,
                placeholder="Optional global prompt",
            ),
            ui.input_checkbox(
                "mock_mode",
                "Use mock responses on failure",
                value=mock_on_fail,
            ),
            ui.input_action_button(
                "save_settings", "Apply settings", class_="btn-primary"
            ),
            class_="modal-body",
        ),
        title="System settings",
        easy_close=True,
        id="settings_modal",
    )
