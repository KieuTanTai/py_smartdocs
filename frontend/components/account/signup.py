from shiny import ui


def signup_modal() -> ui.Tag:
    return ui.modal(
        ui.tags.div(
            ui.input_text("signup_name", "Name"),
            ui.input_text("signup_email", "Email"),
            ui.input_password("signup_password", "Password"),
            ui.input_action_button(
                "signup_submit", "Create account", class_="btn-primary"
            ),
            class_="modal-body",
        ),
        title="Create account",
        easy_close=True,
        id="signup_modal",
    )
