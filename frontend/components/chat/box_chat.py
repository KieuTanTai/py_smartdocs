from shiny import ui

from components.chat.chat_bar import chat_bar_ui


def box_chat_ui(models: list[str]) -> ui.Tag:
    return ui.tags.section(
        ui.tags.div(ui.output_ui("chat_messages"), class_="chat-scroll"),
        chat_bar_ui(models),
        class_="chat-card",
    )
