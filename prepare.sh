#!/bin/bash

python -m venv .venv
source .venv/bin/activate

# pip install -m requirements.txt
pip install playwright pandas openpyxl
pip install flet

playwright install chromium

pip freeze > requirements.txt