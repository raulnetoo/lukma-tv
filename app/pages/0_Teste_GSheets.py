import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Teste GSheets", layout="wide")

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["gsheets"]["spreadsheet_id"])
    abas = [ws.title for ws in sh.worksheets()]
    st.success(f"Consegui abrir a planilha. Abas: {abas}")
except Exception as e:
    st.error("Falha ao autenticar/acessar planilha. Verifique secrets, APIs e compartilhamento.")
    st.exception(e)
