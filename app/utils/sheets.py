import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

@st.cache_resource(show_spinner=False)
def _client():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(
            """
            ❌ Erro ao autenticar no Google Sheets.

            **Verifique:**
            - Se a seção `[gcp_service_account]` em *Secrets* contém o JSON COMPLETO da Service Account.
            - Se o campo `private_key` está no formato correto (com `\\n` em vez de quebras de linha).
            - Se `project_id` e `client_email` estão corretos.
            - Se a planilha foi compartilhada com o `client_email` como **Editor**.
            - Se as APIs **Google Sheets API** e **Google Drive API** estão ativas no Google Cloud.

            Veja os detalhes técnicos nos logs abaixo:
            """
        )
        st.exception(e)
        raise

@st.cache_resource(show_spinner=False)
def _sheet():
    try:
        client = _client()
        return client.open_by_key(st.secrets["gsheets"]["spreadsheet_id"])
    except Exception as e:
        st.error(
            """
            ❌ Erro ao abrir a planilha no Google Sheets.

            **Verifique:**
            - Se `[gsheets].spreadsheet_id` em *Secrets* é o ID correto (parte entre `/d/` e `/edit` da URL).
            - Se a planilha foi compartilhada com o `client_email` da Service Account.
            - Se a planilha contém as abas esperadas (`users`, `news`, `birthdays`, `videos`, `weather_units`, `worldclocks`, `settings`).

            Veja os detalhes técnicos nos logs abaixo:
            """
        )
        st.exception(e)
        raise

def read_df(ws_name: str) -> pd.DataFrame:
    """Lê uma aba da planilha como DataFrame"""
    try:
        ws = _sheet().worksheet(ws_name)
        rows = ws.get_all_records()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Falha ao ler a aba `{ws_name}`. Confirme se a aba existe na planilha.")
        st.exception(e)
        return pd.DataFrame()  # retorna DF vazio para não quebrar o app
