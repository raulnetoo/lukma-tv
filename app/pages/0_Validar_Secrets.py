import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Validador de Secrets", layout="centered")

st.header("🔎 Validador de Secrets / Acesso ao Google Sheets")

pk = st.secrets["gcp_service_account"].get("private_key", "")
st.write("Header OK? ", pk.strip().startswith("-----BEGIN PRIVATE KEY-----"))
st.write("Footer OK? ", pk.strip().endswith("-----END PRIVATE KEY-----"))

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
    st.success(f"✅ Consegui abrir a planilha. Abas: {[ws.title for ws in sh.worksheets()]}")
except Exception as e:
    st.error("❌ Falha ao autenticar/acessar planilha. Revise secrets, compartilhamento e APIs.")
    st.exception(e)
