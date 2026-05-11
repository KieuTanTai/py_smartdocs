from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from shiny import App, reactive, render, ui

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from components.account.login import login_modal
from components.account.signup import signup_modal
from components.chat.box_chat import box_chat_ui
from components.chat.message import build_message, send_message
from components.header import account_dropdown_ui, header_ui
from components.history import history_ui
from components.settings.system_settings import system_settings_modal
from components.sidebars.left import left_sidebar_ui
from components.sidebars.right import right_sidebar_ui
from components.upload_files import upload_modal
from services.api_client import ApiClient, ApiError

DEFAULT_MODELS = [
    "auto",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "ollama:llama3",
    "ollama:mistral",
]

INITIAL_API_BASE_URL = os.getenv("SMARTDOCS_API_BASE_URL", "http://localhost:8000")

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="css/app.css"),
        ui.tags.link(rel="icon", href="favicon.ico"),
        ui.tags.script("""
                        document.addEventListener('click', (event) => {
                            const dropdowns = document.querySelectorAll('details.dropdown');
                            dropdowns.forEach((dropdown) => {
                                if (!dropdown.contains(event.target)) {
                                    dropdown.removeAttribute('open');
                                }
                            });
                        });

                        // Sidebar drag and drop functionality
                        const uploadDragArea = document.getElementById('upload-drag-area');
                        const sidebarFileInput = document.querySelector('input[name="upload_files_sidebar"]');
                        
                        if (uploadDragArea && sidebarFileInput) {
                            uploadDragArea.addEventListener('click', () => {
                                sidebarFileInput.click();
                            });

                            uploadDragArea.addEventListener('dragover', (e) => {
                                e.preventDefault();
                                uploadDragArea.style.borderColor = 'var(--upload-button)';
                                uploadDragArea.style.background = 'rgba(93, 185, 116, 0.15)';
                            });

                            uploadDragArea.addEventListener('dragleave', () => {
                                uploadDragArea.style.borderColor = '';
                                uploadDragArea.style.background = '';
                            });

                            uploadDragArea.addEventListener('drop', (e) => {
                                e.preventDefault();
                                uploadDragArea.style.borderColor = '';
                                uploadDragArea.style.background = '';
                                if (e.dataTransfer.files && sidebarFileInput) {
                                    sidebarFileInput.files = e.dataTransfer.files;
                                    const event = new Event('change', { bubbles: true });
                                    sidebarFileInput.dispatchEvent(event);
                                }
                            });
                        }

                        // Sidebar button click handlers
                        const driveBtnSidebar = document.querySelector('button[id*="upload_source_drive_sidebar"]');
                        const localBtnSidebar = document.querySelector('button[id*="upload_source_local_sidebar"]');
                        
                        if (driveBtnSidebar && sidebarFileInput) {
                            driveBtnSidebar.addEventListener('click', () => {
                                sidebarFileInput.click();
                            });
                        }
                        
                        if (localBtnSidebar && sidebarFileInput) {
                            localBtnSidebar.addEventListener('click', () => {
                                sidebarFileInput.click();
                            });
                        }

                        // Modal button click handlers
                        const driveBtnModal = document.querySelector('button[id*="upload_source_drive"]:not([id*="sidebar"])');
                        const localBtnModal = document.querySelector('button[id*="upload_source_local"]:not([id*="sidebar"])');
                        const modalFileInput = document.querySelector('input[name="upload_files"]');
                        
                        if (driveBtnModal && modalFileInput) {
                            driveBtnModal.addEventListener('click', () => {
                                modalFileInput.click();
                            });
                        }
                        
                        if (localBtnModal && modalFileInput) {
                            localBtnModal.addEventListener('click', () => {
                                modalFileInput.click();
                            });
                        }
                        """),
    ),
    ui.tags.div(
        ui.tags.div(class_="bg-orb orb-1"),
        ui.tags.div(class_="bg-orb orb-2"),
        ui.tags.div(class_="bg-orb orb-3"),
        header_ui(
            INITIAL_API_BASE_URL,
            "auto",
            "",
            True,
        ),
        ui.tags.div(
            ui.tags.aside(left_sidebar_ui(), class_="sidebar left"),
            ui.tags.main(box_chat_ui(DEFAULT_MODELS), class_="main"),
            ui.tags.aside(right_sidebar_ui(), class_="sidebar right"),
            class_="layout",
        ),
        class_="app-shell",
    ),
)


def server(input: Any, output: Any, session: Any) -> None:
    messages = reactive.Value([])
    docs = reactive.Value([])
    history = reactive.Value([])
    metrics = reactive.Value({})
    status = reactive.Value(
        {"label": "Idle", "detail": "No requests yet", "kind": "idle"}
    )
    conversation_id = reactive.Value(None)
    api_base_url = reactive.Value(INITIAL_API_BASE_URL)
    provider = reactive.Value("auto")
    current_model = reactive.Value("auto")
    current_mode = reactive.Value("normal")
    system_prompt = reactive.Value("")
    mock_on_fail = reactive.Value(True)
    current_user = reactive.Value(None)
    upload_source = reactive.Value("local")

    def set_status(label: str, detail: str, kind: str = "info") -> None:
        status.set({"label": label, "detail": detail, "kind": kind})

    def client() -> ApiClient:
        return ApiClient(api_base_url.get())

    def normalize_doc(
        payload: Dict[str, Any], file_info: dict, source: str
    ) -> Dict[str, Any]:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        doc_id = (
            data.get("id")
            or data.get("document_id")
            or data.get("uuid")
            or f"local-{int(time.time())}"
        )
        title = data.get("title") or file_info.get("name") or "Untitled"
        return {
            "id": str(doc_id),
            "title": title,
            "status": data.get("status") or data.get("processing_status") or "uploaded",
            "source": source,
        }

    @render.ui
    def chat_messages() -> ui.Tag:
        items = messages.get()
        if not items:
            return ui.tags.div(
                "Drop a document and start a conversation.", class_="empty-state"
            )

        rows = []
        for msg in items:
            role = msg.get("role", "assistant")
            classes = "message assistant" if role != "user" else "message user"
            meta = msg.get("meta") or {}
            meta_line = None
            if role != "user" and meta:
                parts = []
                if meta.get("provider"):
                    parts.append(f"Provider: {meta['provider']}")
                if meta.get("model"):
                    parts.append(f"Model: {meta['model']}")
                if meta.get("total_ms") is not None:
                    parts.append(f"Total: {meta['total_ms']} ms")
                if meta.get("error"):
                    parts.append("Error: API failed")
                if parts:
                    meta_line = " | ".join(parts)
            rows.append(
                ui.tags.div(
                    ui.tags.p(msg.get("content", ""), class_="message-text"),
                    (
                        ui.tags.div(meta_line, class_="message-meta")
                        if meta_line
                        else None
                    ),
                    class_=classes,
                )
            )

        return ui.tags.div(*rows, class_="message-stack")

    @render.ui
    def history_list() -> ui.Tag:
        return history_ui(history.get())

    @render.ui
    def doc_selector() -> ui.Tag:
        items = docs.get()
        if not items:
            return ui.tags.div("No documents yet.", class_="empty-state")
        choices = {item["id"]: item["title"] for item in items}
        selected = input.selected_docs() or list(choices.keys())[:1]
        return ui.input_select(
            "selected_docs",
            "Selected documents",
            choices=choices,
            selected=selected,
            multiple=True,
        )

    @render.ui
    def status_panel() -> ui.Tag:
        payload = status.get()
        return ui.tags.div(
            ui.tags.span(payload.get("label", ""), class_="status-title"),
            ui.tags.p(payload.get("detail", ""), class_="status-detail"),
            class_=f"status-card {payload.get('kind', 'info')}",
        )

    @render.ui
    def metrics_panel() -> ui.Tag:
        payload = metrics.get()
        if not payload:
            return ui.tags.div("No response yet.", class_="empty-state")
        return ui.tags.div(
            ui.tags.div(
                ui.tags.span("Provider", class_="metric-label"),
                ui.tags.span(payload.get("provider", "-"), class_="metric-value"),
            ),
            ui.tags.div(
                ui.tags.span("Model", class_="metric-label"),
                ui.tags.span(payload.get("model", "-"), class_="metric-value"),
            ),
            ui.tags.div(
                ui.tags.span("Mode", class_="metric-label"),
                ui.tags.span(payload.get("mode", "-"), class_="metric-value"),
            ),
            class_="metrics-grid",
        )

    @render.ui
    def retrieval_panel() -> ui.Tag:
        payload = metrics.get()
        hits = payload.get("hits") or payload.get("retrieval_hits") or []
        if not hits:
            return ui.tags.div("Waiting for retrieval data.", class_="empty-state")
        rows = [ui.tags.li(str(hit)) for hit in hits]
        return ui.tags.ul(*rows, class_="mini-list")

    @render.ui
    def timing_panel() -> ui.Tag:
        payload = metrics.get()
        if not payload:
            return ui.tags.div("No timing data yet.", class_="empty-state")
        items = [
            ("Embed", payload.get("embed_ms")),
            ("Query", payload.get("query_ms")),
            ("Response", payload.get("response_ms")),
            ("Total", payload.get("total_ms")),
        ]
        rows = [
            ui.tags.div(
                ui.tags.span(label, class_="metric-label"),
                ui.tags.span(
                    f"{value} ms" if value is not None else "-", class_="metric-value"
                ),
            )
            for label, value in items
        ]
        return ui.tags.div(*rows, class_="metrics-grid")

    @render.ui
    def model_badge() -> ui.Tag:
        return ui.tags.div(
            f"{provider.get()} / {current_model.get()} / {current_mode.get()}",
            class_="badge",
        )

    @render.ui
    def user_badge() -> ui.Tag:
        user = current_user.get() or "Guest"
        return ui.tags.div(user, class_="badge subtle")

    @render.ui
    def account_menu() -> ui.Tag:
        return account_dropdown_ui(current_user.get() is not None)

    @reactive.effect
    @reactive.event(input.open_settings)
    def _show_settings() -> None:
        ui.modal_show(
            system_settings_modal(
                api_base_url.get(),
                provider.get(),
                system_prompt.get(),
                mock_on_fail.get(),
            )
        )

    @reactive.effect
    @reactive.event(input.save_settings)
    def _save_settings() -> None:
        api_base_url.set(input.api_base_url())
        provider.set(input.provider_select())
        system_prompt.set(input.system_prompt())
        mock_on_fail.set(bool(input.mock_mode()))
        set_status("Settings saved", "Updated system preferences.", "success")
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.mode_select)
    def _mode_changed() -> None:
        current_mode.set(input.mode_select())
        set_status("Mode updated", f"Mode set to {input.mode_select()}", "success")

    @reactive.effect
    @reactive.event(input.model_select)
    def _model_changed() -> None:
        current_model.set(input.model_select())
        set_status("Model updated", f"Model set to {input.model_select()}", "success")

    @reactive.effect
    @reactive.event(input.open_login)
    def _show_login() -> None:
        ui.modal_show(login_modal())

    @reactive.effect
    @reactive.event(input.open_signup)
    def _show_signup() -> None:
        ui.modal_show(signup_modal())

    @reactive.effect
    @reactive.event(input.login_submit)
    def _login() -> None:
        try:
            client().login(input.login_email(), input.login_password())
            current_user.set(input.login_email())
            set_status("Login ok", "Authenticated", "success")
        except ApiError as exc:
            set_status("Login failed", str(exc), "error")
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.signup_submit)
    def _signup() -> None:
        try:
            client().signup(
                input.signup_email(),
                input.signup_password(),
                name=input.signup_name(),
            )
            current_user.set(input.signup_email())
            set_status("Account created", "Signed in", "success")
        except ApiError as exc:
            set_status("Signup failed", str(exc), "error")
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.logout_submit)
    def _logout() -> None:
        current_user.set(None)
        set_status("Logged out", "Signed out", "info")

    @reactive.effect
    @reactive.event(input.open_upload)
    def _show_upload() -> None:
        ui.modal_show(upload_modal())

    @reactive.effect
    @reactive.event(input.upload_source_local)
    def _set_upload_source_local() -> None:
        upload_source.set("local")

    @reactive.effect
    @reactive.event(input.upload_source_drive)
    def _set_upload_source_drive() -> None:
        upload_source.set("drive")

    @reactive.effect
    @reactive.event(input.upload_source_local_sidebar)
    def _set_upload_source_local_sidebar() -> None:
        upload_source.set("local")

    @reactive.effect
    @reactive.event(input.upload_source_drive_sidebar)
    def _set_upload_source_drive_sidebar() -> None:
        upload_source.set("drive")

    @reactive.effect
    @reactive.event(input.upload_files)
    def _handle_upload() -> None:
        files = input.upload_files() or []
        if not files:
            return
        source = upload_source.get()
        current_docs = docs.get()
        for info in files:
            try:
                response = client().upload_document(info, source)
                doc = normalize_doc(response, info, source)
                current_docs = current_docs + [doc]
                set_status("Upload complete", doc["title"], "success")
                try:
                    index_response = client().index_document(doc["id"])
                    doc["status"] = index_response.get("status", "processing")
                except ApiError:
                    pass
            except ApiError as exc:
                current_docs = current_docs + [
                    {
                        "id": f"local-{int(time.time())}",
                        "title": info.get("name", "Untitled"),
                        "status": "uploaded-local",
                        "source": source,
                    }
                ]
                set_status("Upload failed", str(exc), "error")
        docs.set(current_docs)
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.upload_files_sidebar)
    def _handle_upload_sidebar() -> None:
        files = input.upload_files_sidebar() or []
        if not files:
            return
        source = upload_source.get()
        current_docs = docs.get()
        for info in files:
            try:
                response = client().upload_document(info, source)
                doc = normalize_doc(response, info, source)
                current_docs = current_docs + [doc]
                set_status("Upload complete", doc["title"], "success")
                try:
                    index_response = client().index_document(doc["id"])
                    doc["status"] = index_response.get("status", "processing")
                except ApiError:
                    pass
            except ApiError as exc:
                current_docs = current_docs + [
                    {
                        "id": f"local-{int(time.time())}",
                        "title": info.get("name", "Untitled"),
                        "status": "uploaded-local",
                        "source": source,
                    }
                ]
                set_status("Upload failed", str(exc), "error")
        docs.set(current_docs)

    @reactive.effect
    @reactive.event(input.refresh_status)
    def _refresh_status() -> None:
        try:
            health = client().health()
            set_status("Backend ok", str(health), "success")
        except ApiError as exc:
            set_status("Backend down", str(exc), "error")

    @reactive.effect
    @reactive.event(input.send_message)
    def _send_message() -> None:
        text = (input.chat_input() or "").strip()
        if not text:
            return
        selected = input.selected_docs() or []
        if not selected:
            set_status("Select a document", "Pick at least one", "warning")
            return
        current = messages.get()
        current = current + [build_message("user", text)]
        messages.set(current)

        was_new = conversation_id.get() is None
        response = send_message(
            client(),
            conversation_id.get(),
            text,
            selected,
            provider.get(),
            current_model.get(),
            system_prompt.get(),
            current_mode.get(),
            allow_mock=mock_on_fail.get(),
        )
        conversation_id.set(response.get("conversation_id"))
        if was_new and response.get("conversation_id"):
            history.set(
                [
                    {
                        "id": response.get("conversation_id"),
                        "title": text[:42],
                        "when": time.strftime("%H:%M"),
                    }
                ]
                + history.get()
            )
        meta = response.get("metrics") or {}
        if response.get("error"):
            meta = {**meta, "error": response.get("error")}
        messages.set(
            messages.get()
            + [build_message("assistant", response["assistant"], meta=meta)]
        )
        metrics.set(
            {
                **meta,
                "provider": provider.get(),
                "model": current_model.get(),
                "mode": current_mode.get(),
            }
        )
        if response.get("error") and not response.get("used_mock"):
            set_status("Request failed", response.get("error", ""), "error")
        else:
            set_status("Response ready", "Message received", "success")

    @reactive.effect
    @reactive.event(input.clear_chat)
    def _clear_chat() -> None:
        messages.set([])
        metrics.set({})
        conversation_id.set(None)
        set_status("Chat cleared", "Ready for a new session", "info")


app = App(app_ui, server, static_assets=BASE_DIR / "assets")
