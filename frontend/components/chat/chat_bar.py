from typing import List

from shiny import ui

from backend.apps.core.interfaces.dataclass.system.i_provider import IProvider
from components.settings.model_settings import model_settings_ui


def chat_bar_ui(object_providers: List[IProvider]) -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            ui.input_text_area(
                "chat_input",
                None,
                placeholder="Ask about your documents...",
                rows=2,
            ),
            ui.tags.div(
                ui.tags.div(
                    model_settings_ui(object_providers),
                    ui.tags.img(src="separator.png", class_="separator-icon"),
                    ui.input_action_button(
                        "send_message",
                        ui.tags.img(src="send.png", class_="icon"),
                        class_="btn-send",
                    ),
                    class_="chat-controls-inner",
                ),
                class_="chat-controls",
            ),
            class_="chat-input-wrap",
        ),
        class_="chat-bar",
    )
