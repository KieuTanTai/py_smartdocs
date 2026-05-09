from shiny import ui

from components.upload_files import upload_button_ui


def left_sidebar_ui() -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            ui.tags.h3("Sessions"),
            ui.output_ui("history_list"),
            class_="card",
        ),
        ui.tags.div(
            ui.tags.h3("Upload"),
            ui.tags.div(
                ui.tags.img(src="file.png", class_="icon"),
                ui.tags.p("Drag in files or browse", class_="muted"),
                class_="upload-row",
            ),
            upload_button_ui(),
            class_="card",
        ),
        ui.tags.div(
            ui.tags.h3("Documents"),
            ui.tags.p("Select documents for prompt context.", class_="muted"),
            ui.output_ui("doc_selector"),
            class_="card",
        ),
        ui.tags.div(
            ui.tags.h3("Status"),
            ui.output_ui("status_panel"),
            ui.input_action_button(
                "refresh_status", "Ping backend", class_="btn-ghost full-width"
            ),
            class_="card",
        ),
        ui.tags.div(
            ui.input_action_button(
                "clear_chat", "Clear chat", class_="btn-ghost full-width"
            ),
            class_="card",
        ),
        class_="sidebar-content",
    )
