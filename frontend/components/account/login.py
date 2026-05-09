from shiny import ui


def login_modal() -> ui.Tag:
    return ui.modal(
        ui.tags.div(
            ui.input_text("login_email", "Email"),
            ui.input_password("login_password", "Password"),
            ui.input_action_button("login_submit", "Login", class_="btn-primary"),
            class_="modal-body",
        ),
        title="Login",
        easy_close=True,
        id="login_modal",
    )
