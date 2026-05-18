#!/bin/bash
echo "[*] Starting HR Dashboard..."

cd "$(dirname "$0")"
source venv/bin/activate
streamlit run dashboard.py