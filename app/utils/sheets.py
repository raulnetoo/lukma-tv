import time
from typing import Dict, List

import gspread
from gspread.exceptions import APIError
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

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

# ---- Controle de cota: retry exponencial em 429 ----
MAX_RETRIES = 4
BASE_SLEEP = 1.0  # segundos

def _with_retry(fn, *args, **kwargs):
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            msg = str(e)
            is_429 = "429" in msg or "Quota exceeded" in msg
            attempt += 1
            if not is_429 or attempt >= MAX_RETRIES:
                raise
            sleep_for = BASE_SLEEP * (2 ** (attempt - 1))
            time.sleep(sleep_for)
        except Exception:
            # Não insistir em erros não relacionados a cota
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

            Verifique:
            - Secrets: `[gcp_service_account]` completo (JSON).
            - `private_key` formatada (multilinha `\"\"\"...\"\"\"` OU uma linha com `\\n`).
            - `project_id` e `client_email` corretos.
            - Planilha compartilhada com o `client_email` (Editor).
            - APIs Sheets/Drive ativas no GCP.

            Detalhes:
            """
        )
        st.exception(e)
        raise

@st.cache_resource(show_spinner=False)
def _sheet():
    try:
        client = _client()
        return _with_retry(client.open_by_key, st.secrets["gsheets"]["spreadsheet_id"])
    except Exception as e:
        st.error(
            """
            ❌ Erro ao abrir a planilha.

            Verifique:
            - `[gsheets].spreadsheet_id` (trecho entre /d/ e /edit).
            - Compartilhamento com a Service Account.
            - Abas esperadas: users, news, birthdays, videos, weather_units, worldclocks, settings.

            Detalhes:
            """
        )
        st.exception(e)
        raise

# ---------------- Leitura EM LOTE (uma chamada) ----------------
def _ranges_from_names(names: List[str], end_col: str = "Z", end_row: int = 1000) -> List[str]:
    # aspas no título da aba para suportar espaços
    return [f"'{name}'!A1:{end_col}{end_row}" for name in names]

def _values_to_df(values: List[List[str]], ws_name: str) -> pd.DataFrame:
    """Converte o retorno de uma faixa A1 em DataFrame."""
    if not values:
        # vazio -> devolve colunas padrão se conhecidas
        if ws_name in DEFAULT_COLUMNS:
            return pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        return pd.DataFrame()

    headers = [str(h).strip() for h in values[0]] if values else []
    rows = values[1:] if len(values) > 1 else []
    if not headers:
        if ws_name in DEFAULT_COLUMNS:
            return pd.DataFrame(columns=DEFAULT_COLUMNS[ws_name])
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=headers) if rows else pd.DataFrame(columns=headers)
    df.columns = [str(c).strip() for c in df.columns]
    return df

@st.cache_data(ttl=120, show_spinner=False)
def read_tables(ws_names: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Lê várias abas de uma vez via batch_get (reduz drasticamente chamadas).
    Cache de 120s para segurar a cota.
    """
    try:
        sh = _sheet()
        ranges = _ranges_from_names(ws_names, end_col="Z", end_row=1000)
        # batch_get retorna uma lista com os valores de cada range, na ordem
        results = _with_retry(sh.batch_get, ranges)
        out: Dict[str, pd.DataFrame] = {}
        for name, values in zip(ws_names, results):
            out[name] = _values_to_df(values, name)
        # Garante colunas padrão para abas que não vieram
        for name in ws_names:
            if name not in out:
                out[name] = pd.DataFrame(columns=DEFAULT_COLUMNS.get(name, []))
        return out
    except Exception as e:
        st.error("❌ Falha ao ler abas em lote (pode ser cota 429). Usando schema padrão vazio.")
        st.exception(e)
        out = {name: pd.DataFrame(columns=DEFAULT_COLUMNS.get(name, [])) for name in ws_names}
        return out

# ---------------- APIs compatíveis com o restante do projeto ----------------
@st.cache_data(ttl=120, show_spinner=False)
def read_df(ws_name: str) -> pd.DataFrame:
    """Compat: lê uma aba (usa internamente o batch)."""
    tables = read_tables([ws_name])
    return tables.get(ws_name, pd.DataFrame(columns=DEFAULT_COLUMNS.get(ws_name, [])))

def replace_df(ws_name: str, df: pd.DataFrame):
    """Grava a aba inteira (não usa batch para escrita)."""
    try:
        sh = _sheet()
        ws = _with_retry(sh.worksheet, ws_name)
        _with_retry(ws.clear)
        if df is None or df.empty:
            if ws_name in DEFAULT_COLUMNS:
                _with_retry(ws.update, [DEFAULT_COLUMNS[ws_name]])
            else:
                _with_retry(ws.update, [[]])
        else:
            df = df.fillna("")
            _with_retry(ws.update, [df.columns.tolist()] + df.values.tolist())
        # invalida caches de leitura
        read_df.clear()
        read_tables.clear()
    except Exception as e:
        st.error(f"❌ Falha ao gravar na aba `{ws_name}`.")
        st.exception(e)
        raise

def append_row(ws_name: str, row: dict):
    """Acrescenta uma linha respeitando o cabeçalho atual."""
    try:
        sh = _sheet()
        ws = _with_retry(sh.worksheet, ws_name)
        headers = _with_retry(ws.row_values, 1)
        if not headers and ws_name in DEFAULT_COLUMNS:
            headers = DEFAULT_COLUMNS[ws_name]
            _with_retry(ws.update, [headers])
        values = [str(row.get(h, "")) for h in headers]
        _with_retry(ws.append_row, values, value_input_option="USER_ENTERED")
        read_df.clear()
        read_tables.clear()
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
