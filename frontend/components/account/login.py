from shiny import ui


def login_modal() -> ui.Tag:
    return ui.modal(
        ui.tags.div(
            ui.input_text("login_email", "Email"),
            ui.input_password("login_password", "Password"),
            ui.input_action_button(
                "login_submit", "Sign in", class_="btn-primary"
            ),
            ui.tags.div(
                "Don't have an account? ",
                ui.tags.a("Sign up", href="#", id="open_signup_from_login"),
                class_="login-register-link",
            ),
            class_="modal-body",
        ),
        title="Sign in",
        easy_close=True,
        id="login_modal",
    )
