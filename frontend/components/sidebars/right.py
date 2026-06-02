from shiny import ui


def right_sidebar_ui() -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            ui.tags.h3("Response"),
            ui.output_ui("metrics_panel"),
            class_="card",
        ),
        ui.tags.div(
            ui.tags.h3("Retrieval"),
            ui.output_ui("retrieval_panel"),
            class_="card",
        ),
        ui.tags.div(
            ui.tags.h3("Timings"),
            ui.output_ui("timing_panel"),
            class_="card",
        ),
        ui.tags.div(
            ui.tags.h3("Sessions"),
            ui.output_ui("history_list"),
            class_="card",
        ),
        class_="sidebar-content",
    )
