from shiny import ui


def left_sidebar_ui() -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            ui.tags.h3("Upload"),
            ui.tags.div(
                ui.tags.div(
                    ui.tags.img(src="file.png", class_="icon"),
                    ui.tags.div("Drag files here", class_="muted padding-left-8"),
                    class_="upload-drag-area flex-row align-items-center padding-8 border border-radius-8",
                    id="upload-drag-area",
                ),
                ui.tags.div(
                    ui.input_action_button(
                        "upload_source_drive_sidebar",
                        ui.tags.img(src="google-drive.png", class_="icon"),
                        class_="upload-source-btn-sidebar",
                        title="Upload from Drive",
                    ),
                    ui.input_action_button(
                        "upload_source_local_sidebar",
                        ui.tags.img(src="file.png", class_="icon"),
                        class_="upload-source-btn-sidebar",
                        title="Upload from Local",
                    ),
                    class_="upload-buttons-col margin-top-8 margin-bottom-8 flex-row gap-8",
                ),
                class_="upload-wrapper flex-col",
            ),
            ui.input_file(
                "upload_files_sidebar",
                "",
                multiple=True,
                accept="image/jpg, image/png, image/tiff, text/plain, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
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
                "remove_conversation",
                "Remove conversation",
                class_="btn-ghost full-width",
            ),
            class_="card",
        ),
        class_="sidebar-content",
    )
