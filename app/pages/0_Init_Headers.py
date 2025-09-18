import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

DEFAULTS = {
    "users": [
        "username","name","email","password_hash","is_admin",
        "can_news","can_weather","can_birthdays","can_videos",
        "can_worldclocks","can_currencies","active"
    ],
    "news": ["id","title","description","image_url","active","created_at"],
    "birthdays": ["id","name","sector","birthday","photo_url","active"],
    "videos": ["id","title","url","duration_seconds","active"],
    "weather_units": ["id","alias","city","state","latitude","longitude","active"],
    "worldclocks": ["id","label","timezone"],
    "settings": ["key","value"],
}

st.set_page_config(page_title="Init Headers", layout="centered")
st.header("⚙️ Inicializar cabeçalhos nas abas do Google Sheets")

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["gsheets"]["spreadsheet_id"])

    for ws_name, headers in DEFAULTS.items():
        try:
            ws = sh.worksheet(ws_name)
        except Exception:
            ws = sh.add_worksheet(title=ws_name, rows=100, cols=max(1, len(headers)))
        first_row = ws.row_values(1)
        if not first_row:
            ws.update([headers])

    st.success("✅ Cabeçalhos garantidos em todas as abas.")
except Exception as e:
    st.error("❌ Falha ao inicializar cabeçalhos. Confira secrets, compartilhamento e APIs.")
    st.exception(e)
