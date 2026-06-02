from shiny import ui


def history_ui(items: list[dict], active_id: str | None = None) -> ui.Tag:
    if not items:
        return ui.tags.div("No sessions yet.", class_="empty-state")

    rows = []
    for item in items:
        title = item.get("title") or "Untitled"
        is_active = active_id is not None and str(item.get("id")) == str(active_id)
        item_class = "history-item active" if is_active else "history-item"
        rows.append(
            ui.tags.li(
                ui.tags.span(title, class_="history-title"),
                ui.tags.span(item.get("when", ""), class_="history-time"),
                class_=item_class,
            )
        )

    return ui.tags.ul(*rows, class_="history-list")
