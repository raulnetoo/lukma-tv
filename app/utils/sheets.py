import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DEFAULT_COLUMNS = {
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

@st.cache_resource(show_spinner=False)
def _client():
    """Autentica no Google com Service Account vinda do secrets."""
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
            - Se o campo `private_key` está correto (multilinha `\"\"\"...\"\"\"` sem espaços extras, OU uma linha com `\\n`).
            - Se `project_id` e `client_email` estão corretos.
            - Se a planilha foi compartilhada com o `client_email` como **Editor**.
            - Se as APIs **Google Sheets API** e **Google Drive API** estão ativas no Google Cloud.

            Detalhes técnicos nos logs abaixo:
            """
        )
        st.exception(e)
        raise

@st.cache_resource(show_spinner=False)
def _sheet():
    """Abre a planilha pelo ID definido em secrets."""
    try:
        client = _client()
        return client.open_by_key(st.secrets["gsheets"]["spreadsheet_id"])
    except Exception as e:
        st.error(
            """
            ❌ Erro ao abrir a planilha no Google Sheets.

            **Verifique:**
            - `[gsheets].spreadsheet_id` em *Secrets* (é o trecho entre /d/ e /edit).
            - Se a planilha foi compartilhada com o `client_email` da Service Account.
            - Se a planilha contém as abas esperadas:
              `users`, `news`, `birthdays`, `videos`, `weather_units`, `worldclocks`, `settings`.

            Detalhes técnicos nos logs abaixo:
            """
        )
        st.exception(e)
        raise

def read_df(ws_name: str) -> pd.DataFrame:
    """Lê uma aba da planilha como DataFrame. Se estiver vazia, retorna DF com colunas padrão."""
    try:
        ws = _sheet().worksheet(ws_name)
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        # Normaliza nomes de coluna (remove espaços acidentais)
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
        if df.empty and ws_name in DEFAULT_COLUMNS:
            df = pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        return df
    except Exception as e:
        st.error(f"❌ Falha ao ler a aba `{ws_name}`. Confirme se a aba existe na planilha.")
        st.exception(e)
        # Em erro, retorna DF com colunas padrão (se conhecidas) para não quebrar o app
        if ws_name in DEFAULT_COLUMNS:
            return pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        return pd.DataFrame()

def replace_df(ws_name: str, df: pd.DataFrame):
    """Substitui todo o conteúdo da aba pelo DataFrame informado."""
    try:
        ws = _sheet().worksheet(ws_name)
        ws.clear()
        if df is None or df.empty:
            # Mantém apenas cabeçalho se conhecido
            if ws_name in DEFAULT_COLUMNS:
                ws.update([DEFAULT_COLUMNS[ws_name]])
            else:
                ws.update([[]])
            return
        df = df.fillna("")
        ws.update([df.columns.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"❌ Falha ao gravar na aba `{ws_name}`.")
        st.exception(e)
        raise

def append_row(ws_name: str, row: dict):
    """Acrescenta uma linha de acordo com o cabeçalho existente."""
    try:
        ws = _sheet().worksheet(ws_name)
        headers = ws.row_values(1)
        if not headers and ws_name in DEFAULT_COLUMNS:
            headers = DEFAULT_COLUMNS[ws_name]
            ws.update([headers])
        values = [str(row.get(h, "")) for h in headers]
        ws.append_row(values, value_input_option="USER_ENTERED")
    except Exception as e:
        st.error(f"❌ Falha ao inserir linha na aba `{ws_name}`.")
        st.exception(e)
        raise

def upsert_row(ws_name: str, key_field: str, row: dict):
    """Atualiza a linha que tem key_field==row[key_field]; se não existir, insere."""
    try:
        df = read_df(ws_name)
        if ws_name in DEFAULT_COLUMNS and (df.empty or key_field not in df.columns):
            df = pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        key = str(row.get(key_field, ""))
        if key and not df.empty and key_field in df.columns:
            idx = df.index[df[key_field].astype(str) == key]
            if len(idx) > 0:
                for k, v in row.items():
                    if k in df.columns:
                        df.loc[idx[0], k] = v
                replace_df(ws_name, df)
                return
        # Se não achou, insere
        append_row(ws_name, row)
    except Exception as e:
        st.error(f"❌ Falha ao salvar (upsert) na aba `{ws_name}`.")
        st.exception(e)
        raise
