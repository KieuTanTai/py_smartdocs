from typing import List

from shiny import ui

from backend.apps.core.interfaces.dataclass.system.i_provider import IProvider
from components.chat.chat_bar import chat_bar_ui


def box_chat_ui(object_providers: List[IProvider]) -> ui.Tag:
    return ui.tags.section(
        ui.tags.div(ui.output_ui("chat_messages"), class_="chat-scroll"),
        chat_bar_ui(object_providers),
        class_="chat-card",
    )
