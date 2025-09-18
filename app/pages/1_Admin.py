import secrets
import hashlib
import time
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd
import streamlit as st
import requests

from utils.sheets import read_tables, replace_df, upsert_row  # usamos replace_df p/ salvar "em lote"

# --------------------------------- Config ---------------------------------
st.set_page_config(page_title="Painel Admin • Lukma TV", page_icon="⚙️", layout="wide")

# --------------------------------- Helpers de Auth ---------------------------------
# Guardamos hash = sha256(salt + senha)
def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def _make_password_hash(password: str) -> Tuple[str, str]:
    salt = secrets.token_hex(16)
    return salt, _hash_password(password, salt)

def _verify_password(password: str, salt: str, password_hash: str) -> bool:
    return _hash_password(password, salt) == password_hash

def _ensure_users_schema(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "username","name","email","password_hash","password_salt","is_admin",
        "can_news","can_weather","can_birthdays","can_videos",
        "can_worldclocks","can_currencies","active"
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    # garantir todas as colunas
    for c in cols:
        if c not in df.columns:
            df[c] = "" if c not in ["is_admin","can_news","can_weather","can_birthdays","can_videos","can_worldclocks","can_currencies","active"] else False
    # normalizar tipos booleanos
    for c in ["is_admin","can_news","can_weather","can_birthdays","can_videos","can_worldclocks","can_currencies","active"]:
        df[c] = df[c].astype(str).str.lower().isin(["true","1","yes","y","sim"])
    df["username"] = df["username"].astype(str)
    return df[cols]

def _current_user_perms(user_row: pd.Series) -> Dict[str, bool]:
    return {
        "is_admin": bool(user_row.get("is_admin", False)),
        "can_news": bool(user_row.get("can_news", False)),
        "can_weather": bool(user_row.get("can_weather", False)),
        "can_birthdays": bool(user_row.get("can_birthdays", False)),
        "can_videos": bool(user_row.get("can_videos", False)),
        "can_worldclocks": bool(user_row.get("can_worldclocks", False)),
        "can_currencies": bool(user_row.get("can_currencies", False)),
    }

# --------------------------------- Carregamento inicial (uma leitura em lote) ---------------------------------
TABLES = ["users","news","birthdays","videos","weather_units","worldclocks","settings"]
if "cached_tables" not in st.session_state:
    st.session_state["cached_tables"] = read_tables(TABLES)
tables = st.session_state["cached_tables"]

# Normaliza USERS
users_df = _ensure_users_schema(tables.get("users", pd.DataFrame()))

# --------------------------------- Login / Logout ---------------------------------
def _set_logged_user(u: pd.Series):
    st.session_state["auth_user"] = {
        "username": u.get("username",""),
        "name": u.get("name",""),
        "is_admin": bool(u.get("is_admin", False)),
        "can_news": bool(u.get("can_news", False)),
        "can_weather": bool(u.get("can_weather", False)),
        "can_birthdays": bool(u.get("can_birthdays", False)),
        "can_videos": bool(u.get("can_videos", False)),
        "can_worldclocks": bool(u.get("can_worldclocks", False)),
        "can_currencies": bool(u.get("can_currencies", False)),
    }

def _logout():
    for k in ["auth_user"]:
        if k in st.session_state:
            del st.session_state[k]
    st.success("Sessão encerrada.")
    st.cache_data.clear()
    st.cache_resource.clear()
    time.sleep(0.5)
    st.rerun()

def _login_form():
    st.title("🔐 Login — Painel Admin")
    st.caption("Use seu usuário e senha. O administrador pode criar novos usuários.")
    username = st.text_input("Usuário", key="login_username")
    password = st.text_input("Senha", type="password", key="login_password")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Entrar", type="primary"):
            if users_df.empty:
                st.error("Não há usuários cadastrados. Peça ao administrador para criar um usuário.")
                return
            urow = users_df[users_df["username"].astype(str) == str(username)].head(1)
            if urow.empty:
                st.error("Usuário ou senha inválidos.")
                return
            u = urow.iloc[0]
            if not bool(u.get("active", True)):
                st.error("Usuário inativo.")
                return
            salt = str(u.get("password_salt",""))
            pwhash = str(u.get("password_hash",""))
            if salt == "" or pwhash == "":
                st.error("Usuário sem senha definida. Contate o administrador.")
                return
            if _verify_password(password, salt, pwhash):
                _set_logged_user(u)
                st.success(f"Bem-vindo, {u.get('name') or username}!")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    with col2:
        if st.button("Cancelar"):
            st.stop()

# Se não logado → mostra login
if "auth_user" not in st.session_state:
    # Caso especial: se não existir nenhum usuário, exibe wizard de criação do primeiro admin
    if users_df.empty:
        st.title("👤 Criar Administrador (primeiro acesso)")
        st.info("Nenhum usuário encontrado. Crie o **primeiro administrador**.")
        u = st.text_input("Usuário (login)")
        nm = st.text_input("Nome completo")
        em = st.text_input("Email")
        pw1 = st.text_input("Senha", type="password")
        pw2 = st.text_input("Confirmar senha", type="password")
        if st.button("Criar administrador", type="primary"):
            if not u or not pw1 or pw1 != pw2:
                st.error("Usuário e senhas são obrigatórios, e as senhas precisam coincidir.")
            else:
                salt, pwh = _make_password_hash(pw1)
                # Monta DF novo
                new_users = pd.DataFrame([{
                    "username": u, "name": nm, "email": em,
                    "password_hash": pwh, "password_salt": salt,
                    "is_admin": True,
                    "can_news": True, "can_weather": True, "can_birthdays": True,
                    "can_videos": True, "can_worldclocks": True, "can_currencies": True,
                    "active": True
                }])
                try:
                    replace_df("users", new_users)
                    st.session_state["cached_tables"]["users"] = new_users
                    st.success("Administrador criado! Faça login para continuar.")
                    time.sleep(0.4)
                    st.rerun()
                except Exception as e:
                    st.error("Falha ao criar administrador.")
                    st.exception(e)
    else:
        _login_form()
        st.stop()

# Logado
auth = st.session_state["auth_user"]
perms = _current_user_perms(pd.Series(auth))
st.sidebar.success(f"Logado como: **{auth['username']}**")
if st.sidebar.button("Sair", use_container_width=True):
    _logout()

st.title("⚙️ Painel de Administração — Lukma TV")

# --------------------------------- Utilidades de UI / Salvar ---------------------------------
def _bool_cols(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.lower().isin(["true","1","yes","y","sim"])
    return df

def _save_table(ws_name: str, edited_df: pd.DataFrame, enforce_cols=None):
    try:
        if edited_df is None:
            edited_df = pd.DataFrame()
        # normalizações
        edited_df.columns = [str(c).strip() for c in edited_df.columns]
        if enforce_cols:
            for c in enforce_cols:
                if c not in edited_df.columns:
                    edited_df[c] = ""
            edited_df = edited_df[enforce_cols]
        replace_df(ws_name, edited_df.fillna(""))
        # atualiza cache local
        st.session_state["cached_tables"][ws_name] = edited_df
        st.success("Alterações salvas com sucesso.")
    except Exception as e:
        st.error(f"Falha ao salvar a aba `{ws_name}`.")
        st.exception(e)

def _data_editor(df: pd.DataFrame, key: str, height: int = 340):
    cfg = {
        "changed": st.column_config.CheckboxColumn("active", help="Marque para ativar")
    } if "active" in df.columns else None
    return st.data_editor(
        df, key=key, use_container_width=True, height=height,
        num_rows="dynamic",
        column_config=cfg
    )

# --------------------------------- Abas / Permissões ---------------------------------
tabs = []
tab_labels = []

if perms["can_news"]:          tab_labels.append("📰 Notícias")
if perms["can_birthdays"]:     tab_labels.append("🎉 Aniversariantes")
if perms["can_videos"]:        tab_labels.append("🎬 Vídeos")
if perms["can_weather"]:       tab_labels.append("🌦️ Unidades (Clima)")
if perms["can_worldclocks"]:   tab_labels.append("🕒 Relógios")
if perms["can_currencies"]:    tab_labels.append("💱 Moedas (Settings)")

if perms["is_admin"]:
    tab_labels.append("👥 Usuários (Admin)")

if not tab_labels:
    st.warning("Seu usuário não possui permissões para editar nenhum conteúdo. Contate o administrador.")
    st.stop()

tabs = st.tabs(tab_labels)

# Para ler os dados atuais do cache
def _get_table(name: str, ensure_cols=None) -> pd.DataFrame:
    df = st.session_state["cached_tables"].get(name, pd.DataFrame())
    if ensure_cols:
        for c in ensure_cols:
            if c not in df.columns:
                df[c] = ""
        df = df[ensure_cols]
    return df.copy()

# --------------------------------- Tab: Notícias ---------------------------------
idx = 0
if perms["can_news"]:
    with tabs[idx]:
        st.subheader("📰 Notícias da empresa")
        df = _get_table("news", ["id","title","description","image_url","active","created_at"])
        if df.empty:
            df = pd.DataFrame(columns=["id","title","description","image_url","active","created_at"])
        # id e created_at helpers
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("➕ Adicionar notícia"):
                new = {"id": str(int(time.time())), "title":"", "description":"", "image_url":"",
                       "active": True, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        with colB:
            st.caption("Use o editor abaixo para alterar títulos, descrições e imagens. Marque/desmarque **active**.")
        edited = _data_editor(df, key="news_editor", height=420)
        if st.button("💾 Salvar notícias", type="primary"):
            edited = _bool_cols(edited, ["active"])
            _save_table("news", edited, ["id","title","description","image_url","active","created_at"])
    idx += 1

# --------------------------------- Tab: Aniversariantes ---------------------------------
if perms["can_birthdays"]:
    with tabs[idx]:
        st.subheader("🎉 Aniversariantes do mês")
        df = _get_table("birthdays", ["id","name","sector","birthday","photo_url","active"])
        if df.empty:
            df = pd.DataFrame(columns=["id","name","sector","birthday","photo_url","active"])
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("➕ Adicionar aniversariante"):
                new = {"id": str(int(time.time())), "name":"", "sector":"", "birthday":"", "photo_url":"", "active": True}
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        with colB:
            st.caption("Formato de **birthday** recomendado: YYYY-MM-DD (ex.: 2025-09-30).")
        edited = _data_editor(df, key="birth_editor", height=420)
        if st.button("💾 Salvar aniversariantes", type="primary"):
            edited = _bool_cols(edited, ["active"])
            _save_table("birthdays", edited, ["id","name","sector","birthday","photo_url","active"])
    idx += 1

# --------------------------------- Tab: Vídeos ---------------------------------
if perms["can_videos"]:
    with tabs[idx]:
        st.subheader("🎬 Vídeos institucionais")
        df = _get_table("videos", ["id","title","url","duration_seconds","active"])
        if df.empty:
            df = pd.DataFrame(columns=["id","title","url","duration_seconds","active"])
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("➕ Adicionar vídeo"):
                new = {"id": str(int(time.time())), "title":"", "url":"", "duration_seconds":"30", "active": True}
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        with colB:
            st.caption("Suporta **YouTube** (autoplay) e arquivos **.mp4/.webm/.ogg**.")
        edited = _data_editor(df, key="videos_editor", height=420)
        if st.button("💾 Salvar vídeos", type="primary"):
            edited = _bool_cols(edited, ["active"])
            # normaliza duração
            if "duration_seconds" in edited.columns:
                edited["duration_seconds"] = edited["duration_seconds"].apply(lambda x: str(x).strip() if pd.notna(x) else "30")
            _save_table("videos", edited, ["id","title","url","duration_seconds","active"])
    idx += 1

# --------------------------------- Tab: Unidades (Clima) ---------------------------------
def _geocode_city(city: str):
    try:
        g = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "pt"},
            timeout=10
        ).json()
        if g.get("results"):
            return g["results"][0]["latitude"], g["results"][0]["longitude"]
    except Exception:
        pass
    return None, None

if perms["can_weather"]:
    with tabs[idx]:
        st.subheader("🌦️ Unidades (Previsão do tempo)")
        df = _get_table("weather_units", ["id","alias","city","state","latitude","longitude","active"])
        if df.empty:
            df = pd.DataFrame(columns=["id","alias","city","state","latitude","longitude","active"])
        colA, colB, colC = st.columns([1,1,1])
        with colA:
            if st.button("➕ Adicionar unidade"):
                new = {"id": str(int(time.time())), "alias":"", "city":"", "state":"",
                       "latitude":"", "longitude":"", "active": True}
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        with colB:
            st.caption("Preencha **city** e use **Geocodificar vazios** para obter latitude/longitude.")
        with colC:
            if st.button("📍 Geocodificar vazios"):
                for i, row in df.iterrows():
                    if (not str(row.get("latitude","")).strip() or not str(row.get("longitude","")).strip()) and str(row.get("city","")).strip():
                        lat, lon = _geocode_city(str(row["city"]))
                        if lat and lon:
                            df.at[i, "latitude"] = lat
                            df.at[i, "longitude"] = lon
                st.success("Geocodificação concluída (onde possível).")
        edited = _data_editor(df, key="weather_editor", height=420)
        if st.button("💾 Salvar unidades", type="primary"):
            edited = _bool_cols(edited, ["active"])
            _save_table("weather_units", edited, ["id","alias","city","state","latitude","longitude","active"])
    idx += 1

# --------------------------------- Tab: Relógios ---------------------------------
if perms["can_worldclocks"]:
    with tabs[idx]:
        st.subheader("🕒 Relógios (World Clocks)")
        df = _get_table("worldclocks", ["id","label","timezone"])
        if df.empty:
            df = pd.DataFrame(columns=["id","label","timezone"])
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("➕ Adicionar relógio"):
                new = {"id": str(int(time.time())), "label":"", "timezone":"America/Sao_Paulo"}
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        with colB:
            st.caption("Ex.: America/Sao_Paulo, America/New_York, Asia/Hong_Kong")
        edited = _data_editor(df, key="clocks_editor", height=420)
        if st.button("💾 Salvar relógios", type="primary"):
            _save_table("worldclocks", edited, ["id","label","timezone"])
    idx += 1

# --------------------------------- Tab: Moedas (Settings) ---------------------------------
if perms["can_currencies"]:
    with tabs[idx]:
        st.subheader("💱 Moedas (Settings)")
        st.caption("Guarde chaves e configurações simples. Ex.: `currency_refresh_minutes = 5`")
        df = _get_table("settings", ["key","value"])
        if df.empty:
            df = pd.DataFrame(columns=["key","value"])
        edited = _data_editor(df, key="settings_editor", height=320)
        if st.button("💾 Salvar settings", type="primary"):
            _save_table("settings", edited, ["key","value"])
    idx += 1

# --------------------------------- Tab: Usuários (Admin) ---------------------------------
if perms["is_admin"]:
    with tabs[idx]:
        st.subheader("👥 Usuários (somente administrador)")

        df = users_df.copy()  # já normalizado
        # Editor principal (oculta hash/salt, mostra toggles)
        show_cols = [
            "username","name","email","is_admin","can_news","can_weather",
            "can_birthdays","can_videos","can_worldclocks","can_currencies","active"
        ]
        st.markdown("#### Lista e permissões")
        edited_view = _data_editor(df[show_cols], key="users_editor_view", height=420)

        colA, colB, colC = st.columns([1,1,1])
        with colA:
            st.markdown("#### ➕ Criar novo usuário")
            nu = st.text_input("Usuário (login)", key="new_u")
            nm = st.text_input("Nome completo", key="new_n")
            em = st.text_input("Email", key="new_e")
            pw1 = st.text_input("Senha", type="password", key="new_p1")
            pw2 = st.text_input("Confirmar senha", type="password", key="new_p2")
            if st.button("Criar usuário", type="primary"):
                if not nu or not pw1 or pw1 != pw2:
                    st.error("Usuário e senhas são obrigatórios, e as senhas precisam coincidir.")
                elif (df["username"].astype(str) == nu).any():
                    st.error("Usuário já existe.")
                else:
                    salt, pwh = _make_password_hash(pw1)
                    new_row = {
                        "username": nu, "name": nm, "email": em,
                        "password_hash": pwh, "password_salt": salt,
                        "is_admin": False,
                        "can_news": False, "can_weather": False, "can_birthdays": False,
                        "can_videos": False, "can_worldclocks": False, "can_currencies": False,
                        "active": True
                    }
                    # Atualiza DF completo
                    df2 = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    try:
                        # Salva tabela completa de users (incluindo hash/salt)
                        replace_df("users", df2.fillna(""))
                        st.session_state["cached_tables"]["users"] = df2
                        st.success("Usuário criado.")
                        time.sleep(0.4)
                        st.rerun()
                    except Exception as e:
                        st.error("Falha ao criar usuário.")
                        st.exception(e)

        with colB:
            st.markdown("#### 🔁 Redefinir senha de um usuário")
            sel_user = st.selectbox("Selecione o usuário", [""] + df["username"].tolist(), key="pw_user")
            np1 = st.text_input("Nova senha", type="password", key="pw_n1")
            np2 = st.text_input("Confirmar nova senha", type="password", key="pw_n2")
            if st.button("Redefinir senha"):
                if not sel_user or not np1 or np1 != np2:
                    st.error("Selecione um usuário e informe a nova senha (as duas iguais).")
                else:
                    salt, pwh = _make_password_hash(np1)
                    df.loc[df["username"] == sel_user, "password_salt"] = salt
                    df.loc[df["username"] == sel_user, "password_hash"] = pwh
                    try:
                        replace_df("users", df.fillna(""))
                        st.session_state["cached_tables"]["users"] = df
                        st.success("Senha alterada.")
                    except Exception as e:
                        st.error("Falha ao redefinir senha.")
                        st.exception(e)

        with colC:
            st.markdown("#### 🗑️ Inativar/Reativar usuário")
            sel_user2 = st.selectbox("Usuário", [""] + df["username"].tolist(), key="act_user")
            active_toggle = st.checkbox("Ativo", value=True, key="act_toggle")
            if st.button("Aplicar ativo/inativo"):
                if not sel_user2:
                    st.error("Selecione o usuário.")
                else:
                    df.loc[df["username"] == sel_user2, "active"] = bool(active_toggle)
                    try:
                        replace_df("users", df.fillna(""))
                        st.session_state["cached_tables"]["users"] = df
                        st.success("Status atualizado.")
                    except Exception as e:
                        st.error("Falha ao atualizar status.")
                        st.exception(e)

        st.markdown("---")
        st.markdown("#### 💾 Salvar permissões (lista acima)")
        if st.button("Salvar permissões dos usuários", type="primary"):
            # aplicamos as permissões editadas na view ao DF completo
            for c in show_cols:
                if c in ["username","name","email"]:
                    df[c] = edited_view[c]
                else:
                    df[c] = edited_view[c].astype(str).str.lower().isin(["true","1","yes","y","sim"])
            try:
                replace_df("users", df.fillna(""))
                st.session_state["cached_tables"]["users"] = df
                st.success("Permissões salvas.")
            except Exception as e:
                st.error("Falha ao salvar permissões.")
                st.exception(e)
