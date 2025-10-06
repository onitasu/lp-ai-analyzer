#!/bin/bash
# Streamlit Community Cloud用の起動スクリプト

echo "Checking Playwright installation..."

# Playwrightブラウザがインストールされているか確認
if [ ! -d "$HOME/.cache/ms-playwright/chromium"* ]; then
    echo "Installing Playwright browsers..."
    playwright install chromium
else
    echo "Playwright browsers already installed."
fi

echo "Starting Streamlit app..."
streamlit run app.py

