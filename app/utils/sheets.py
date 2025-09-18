import time
import gspread
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

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

MAX_RETRIES = 3
BASE_SLEEP = 1.2  # segundos (exponential backoff)

def _with_retry(fn, *args, **kwargs):
    """Executa função com retry exponencial em caso de 429 ou erros transitórios."""
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            msg = str(e)
            is_429 = "429" in msg or "Quota exceeded" in msg
            attempt += 1
            if attempt >= MAX_RETRIES or not is_429:
                raise
            sleep_for = BASE_SLEEP * (2 ** (attempt - 1))
            time.sleep(sleep_for)
        except Exception:
            # erros permanentes não devem ficar em loop
            raise

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
            - `[gcp_service_account]` completo (JSON) em *Secrets*.
            - `private_key` corretamente formatada (multilinha `"""..."""` OU uma linha com `\\n`).
            - `project_id` e `client_email` corretos.
            - Planilha compartilhada com o `client_email` (Editor).
            - APIs **Sheets** e **Drive** ativas no Google Cloud.

            Detalhes técnicos:
            """
        )
        st.exception(e)
        raise

@st.cache_resource(show_spinner=False)
def _sheet():
    """Abre a planilha pelo ID definido em secrets."""
    try:
        client = _client()
        return _with_retry(client.open_by_key, st.secrets["gsheets"]["spreadsheet_id"])
    except Exception as e:
        st.error(
            """
            ❌ Erro ao abrir a planilha do Google Sheets.

            **Verifique:**
            - `[gsheets].spreadsheet_id` (trecho entre /d/ e /edit).
            - Compartilhamento com o `client_email` da Service Account.
            - Abas esperadas: `users`, `news`, `birthdays`, `videos`, `weather_units`, `worldclocks`, `settings`.

            Detalhes técnicos:
            """
        )
        st.exception(e)
        raise

@st.cache_data(ttl=60, show_spinner=False)  # cache por 60s para reduzir leituras
def read_df(ws_name: str) -> pd.DataFrame:
    """Lê uma aba como DataFrame. Usa retry+cache e retorna colunas padrão se vazio."""
    try:
        sh = _sheet()
        ws = _with_retry(sh.worksheet, ws_name)
        rows = _with_retry(ws.get_all_records)
        df = pd.DataFrame(rows)
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
        if df.empty and ws_name in DEFAULT_COLUMNS:
            df = pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        return df
    except Exception as e:
        st.error(f"❌ Falha ao ler a aba `{ws_name}`. Pode ser cota (429) ou aba ausente.")
        st.exception(e)
        # retorna colunas padrão (se houver) para não quebrar o app
        if ws_name in DEFAULT_COLUMNS:
            return pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        return pd.DataFrame()

def replace_df(ws_name: str, df: pd.DataFrame):
    """Substitui todo o conteúdo da aba pelo DataFrame informado."""
    try:
        sh = _sheet()
        ws = _with_retry(sh.worksheet, ws_name)
        _with_retry(ws.clear)
        if df is None or df.empty:
            if ws_name in DEFAULT_COLUMNS:
                _with_retry(ws.update, [DEFAULT_COLUMNS[ws_name]])
            else:
                _with_retry(ws.update, [[]])
            return
        df = df.fillna("")
        _with_retry(ws.update, [df.columns.tolist()] + df.values.tolist())
        read_df.clear()  # invalida cache de leitura dessa aba
    except Exception as e:
        st.error(f"❌ Falha ao gravar na aba `{ws_name}`.")
        st.exception(e)
        raise

def append_row(ws_name: str, row: dict):
    """Acrescenta uma linha de acordo com o cabeçalho existente."""
    try:
        sh = _sheet()
        ws = _with_retry(sh.worksheet, ws_name)
        headers = _with_retry(ws.row_values, 1)
        if not headers and ws_name in DEFAULT_COLUMNS:
            headers = DEFAULT_COLUMNS[ws_name]
            _with_retry(ws.update, [headers])
        values = [str(row.get(h, "")) for h in headers]
        _with_retry(ws.append_row, values, value_input_option="USER_ENTERED")
        read_df.clear()  # invalida cache
    except Exception as e:
        st.error(f"❌ Falha ao inserir linha na aba `{ws_name}`.")
        st.exception(e)
        raise

def upsert_row(ws_name: str, key_field: str, row: dict):
    """Atualiza a linha com key_field==row[key_field]; se não existir, insere."""
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
        append_row(ws_name, row)
    except Exception as e:
        st.error(f"❌ Falha ao salvar (upsert) na aba `{ws_name}`.")
        st.exception(e)
        raise
