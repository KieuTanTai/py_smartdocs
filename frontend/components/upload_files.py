from shiny import ui


def upload_button_ui() -> ui.Tag:
    return ui.input_action_button(
        "open_upload",
        ui.tags.img(src="upload.png", class_="icon"),
        class_="upload-btn",
    )


def upload_modal() -> ui.Tag:
    return ui.modal(
        ui.tags.div(
            ui.tags.div(
                ui.input_action_button(
                    "upload_source_local",
                    ui.tags.img(src="file.png", class_="icon"),
                    class_="upload-source-btn",
                    title="Local storage",
                ),
                ui.input_action_button(
                    "upload_source_drive",
                    ui.tags.img(src="google-drive.png", class_="icon"),
                    class_="upload-source-btn",
                    title="Google Drive",
                ),
                class_="upload-source-buttons",
            ),
            class_="modal-body",
        ),
        title="Upload documents",
        easy_close=True,
        id="upload_modal",
    )
