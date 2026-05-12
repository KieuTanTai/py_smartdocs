# README

## Installation

1. Create virtual environment using python/python3:
    python3 -m venv ./.venv

2. Using Virtual environment:
    - `Window`: ./.venv/Scripts/active
    - `Linux`: source ./.venv/bin/activate

3. Install requirement packages by `requirements/dev.txt` on both frontend and backend folders:
    - `frontend`: pip install -r frontend/requirements/dev.txt
    - `backend` : pip install -r backend/requirements/dev.txt

## Run code

    - `frontend` : python3 -m shiny run --app-dir  frontend --reload
    - `test file`: python3 -m frontend.tests.{file name}

### NOTE
    
    - Replace path on files test to real path on your device
    - read file .env.example and create your own file !
    