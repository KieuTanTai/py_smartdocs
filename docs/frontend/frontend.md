# index web UI

## Purpose

frontend ui for web design by shiny package, handle request and give it for backend.

## Main Files

- `frontend/index.py` for handle import main UI (left/right sidebar, header, main chat,...)
- `frontend/components/chat/message.py` for handle state chat, handle send request for backend and get response (response have footer is info of model chat)
- `frontend/components/chat/chat_bar.py` for handle chat prompt, just have allowed chat if has selected any file, include `frontend/components/settings/model_settings.py` on left of send message button (have separate line between its).
- `frontend/components/chat/box_chat.py` for handle scroll box chat, import `frontend/components/chat/chat_bar.py` for showing and calc height of box include chat bar.
- `frontend/components/history.py` for handle history sessions chat and history processed documents
- `frontend/components/settings/system_settings.py` for handle settings popup, send request settings to backend
- `frontend/components/settings/model_settings.py` for handle model settings horizontal block (flex like, left button will showing form choose mode chat when clicked, right is show model list when clicked), send model name, mode chat (normal chat, cli termux chat mode) - default is normal, choose mode before start session and can't change mode on this session.
- `frontend/components/upload_files.py` for handle popup form upload files (upload form drive, local storage), exit form after upload file (not need upload buttons, just choose file to upload) and auto process after uploaded.
- `frontend/components/sidebars/left.py` for handle left sidebar blocks, includes history block, upload files block, process button, status, block processed docs, remove conversation buttons.
- `frontend/components/sidbars/right.py` for handle show status and info after any chat request and response, showing retrieval score (sorted), hits, chunks, documents on chunks, process time, embedded time, query time, response time, total times (ms)
- `frontend/components/header.py` for handle header of website, flex layout, have web icon, web name on left side, button setting for calling `frontend/components/settings/system_settings.py` when clicked, circle button with account avatar (default using on `frontend/assets/`).

## Constraint

### Systems

- Using Shiny package*
- Create css file on `frontend/assets/css/`
- Using resource from `frontend/assets/` if have
- Separate logic code with ui code
- Prefer using flex layout for design UI

### UI

- Mode button, Model button, account button using dropdown list layout, size of buttons flexing with content (max with 100px), icon is center of button.
- System settings button is overlay form.
- Mode button, Model button, send button is child of chat input container, chat_input is 100% width relative to chat-bar and cant resize (like github copilot) with text - icon is center, if text is too long so using "..." css style for it. Mode button, Model button on left side of send button (using separate icon for separate its)
- favicon.ico is the same with `frontend/assets/analysis.png`, using for icon of this website on tabs bar.
- Prevent change color from any extensions
- All forms using flex style with center both horizontal and vertical for prevent breaking forms

### Behavior

- Click outside dropdown form will close form
- Overlay form have close button (x) - red color

#### color pallate

  --main: #22262b;
  --bg-1: #22262b;
  --bg-2: #1c2024;
  --ink: #ffffff;
  --muted: #b8bcc1;
  --accent: #ef6b4f;
  --accent-2: #2a7f77;
  --button:  #282A2C;
  --function-button: #4A595A;
  --upload-button: #5db974;
  --panel: rgba(51, 55, 59, 0.78);
  --panel-strong: rgba(51, 55, 59, 0.9);
  --panel-border: rgba(255, 255, 255, 0.12);
  --shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
