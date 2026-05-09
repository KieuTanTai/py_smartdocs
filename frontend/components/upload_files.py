from shiny import ui


def upload_button_ui() -> ui.Tag:
    return ui.input_action_button(
        "open_upload",
        "Upload files",
        class_="btn-primary full-width",
    )


def upload_modal() -> ui.Tag:
    return ui.modal(
        ui.tags.div(
            ui.input_select(
                "upload_source",
                "Source",
                choices={"local": "Local storage", "drive": "Drive"},
                selected="local",
            ),
            ui.input_file(
                "upload_files",
                "Choose files",
                multiple=True,
            ),
            ui.tags.p(
                "Files upload immediately after selection.",
                class_="hint",
            ),
            class_="modal-body",
        ),
        title="Upload documents",
        easy_close=True,
        id="upload_modal",
    )
