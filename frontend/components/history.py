from shiny import ui


def history_ui(items: list[dict]) -> ui.Tag:
    if not items:
        return ui.tags.div("No sessions yet.", class_="empty-state")

    rows = []
    for item in items:
        title = item.get("title") or "Untitled"
        rows.append(
            ui.tags.li(
                ui.tags.span(title, class_="history-title"),
                ui.tags.span(item.get("when", ""), class_="history-time"),
            )
        )

    return ui.tags.ul(*rows, class_="history-list")
