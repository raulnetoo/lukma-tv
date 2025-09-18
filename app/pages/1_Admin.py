import streamlit as st
import pandas as pd
from utils.auth import build_authenticator, is_admin, check_perm, create_user, set_password
from utils.sheets import read_df, replace_df, append_row, upsert_row

st.set_page_config(page_title="Painel - Lukma TV", page_icon="🔐", layout="wide")

authenticator = build_authenticator()
name, auth_status, username = authenticator.login("Entrar", "main")

if auth_status is False:
    st.error("Usuário ou senha inválidos.")
elif auth_status is None:
    st.info("Informe suas credenciais.")
else:
    authenticator.logout("Sair", "sidebar")
    st.sidebar.success(f"Olá, {name} (@{username})")

    admin = is_admin(username)

    tabs = []
    if admin or check_perm(username, "can_news"): tabs.append("Notícias")
    if admin or check_perm(username, "can_weather"): tabs.append("Previsão")
    if admin or check_perm(username, "can_birthdays"): tabs.append("Aniversariantes")
    if admin or check_perm(username, "can_videos"): tabs.append("Vídeos")
    if admin or check_perm(username, "can_worldclocks") or check_perm(username, "can_currencies"): tabs.append("Horas & Moedas")
    if admin: tabs.append("Usuários (Admin)")

    cur = st.tabs(tabs) if tabs else []

    idx = 0
    if "Notícias" in tabs:
        with cur[idx]; idx += 1
            st.header("📰 Notícias")
            df = read_df("news")
            st.dataframe(df)
            with st.form("form_news_add"):
                st.subheader("Adicionar/Atualizar")
                idv = st.text_input("ID (use um identificador único)")
                title = st.text_input("Título")
                desc = st.text_area("Descrição breve", max_chars=240)
                img = st.text_input("URL da imagem")
                active = st.checkbox("Ativo", value=True)
                if st.form_submit_button("Salvar"):
                    upsert_row("news", "id", {
                        "id": idv, "title": title, "description": desc, "image_url": img,
                        "active": str(active), "created_at": pd.Timestamp.now().isoformat()
                    })
                    st.success("Notícia salva.")

    if "Previsão" in tabs:
        with cur[idx]; idx += 1
            st.header("🌤️ Unidades (Previsão do Tempo)")
            df = read_df("weather_units")
            st.dataframe(df)
            with st.form("form_wu"):
                st.subheader("Adicionar/Atualizar unidade")
                idv = st.text_input("ID")
                alias = st.text_input("Alias (ex: Lukma RP)")
                city = st.text_input("Cidade", value="São José do Rio Preto")
                state = st.text_input("UF", value="SP")
                lat = st.text_input("Latitude (opcional)")
                lon = st.text_input("Longitude (opcional)")
                active = st.checkbox("Ativo", value=True)
                if st.form_submit_button("Salvar"):
                    upsert_row("weather_units","id",{
                        "id": idv, "alias": alias, "city": city, "state": state,
                        "latitude": lat, "longitude": lon, "active": str(active)
                    })
                    st.success("Unidade salva.")

    if "Aniversariantes" in tabs:
        with cur[idx]; idx += 1
            st.header("🎉 Aniversariantes")
            df = read_df("birthdays")
            st.dataframe(df)
            with st.form("form_bd"):
                st.subheader("Adicionar/Atualizar")
                idv = st.text_input("ID")
                namev = st.text_input("Nome")
                sector = st.text_input("Setor")
                birthday = st.date_input("Dia do aniversário")
                photo = st.text_input("URL da foto")
                active = st.checkbox("Ativo", value=True)
                if st.form_submit_button("Salvar"):
                    upsert_row("birthdays","id",{
                        "id": idv, "name": namev, "sector": sector,
                        "birthday": birthday.isoformat(),
                        "photo_url": photo, "active": str(active)
                    })
                    st.success("Aniversariante salvo.")

    if "Vídeos" in tabs:
        with cur[idx]; idx += 1
            st.header("🎬 Vídeos institucionais")
            df = read_df("videos")
            st.dataframe(df)
            with st.form("form_vid"):
                st.subheader("Adicionar/Atualizar")
                idv = st.text_input("ID")
                title = st.text_input("Título")
                url = st.text_input("URL (YouTube ou MP4)")
                dur = st.number_input("Duração (segundos) — usado para pular ao próximo", min_value=5, value=30)
                active = st.checkbox("Ativo", value=True)
                if st.form_submit_button("Salvar"):
                    upsert_row("videos","id",{
                        "id": idv, "title": title, "url": url, "duration_seconds": dur, "active": str(active)
                    })
                    st.success("Vídeo salvo.")

    if "Horas & Moedas" in tabs:
        with cur[idx]; idx += 1
            st.header("🕒 Horas mundiais / 💱 Moedas")
            df = read_df("worldclocks")
            st.dataframe(df)
            with st.form("form_wc"):
                st.subheader("Adicionar/Atualizar relógio")
                idv = st.text_input("ID")
                label = st.text_input("Rótulo", value="Brasília")
                tz = st.text_input("Timezone (IANA)", value="America/Sao_Paulo")
                if st.form_submit_button("Salvar"):
                    upsert_row("worldclocks","id",{"id": idv, "label": label, "timezone": tz})
                    st.success("Relógio salvo.")
            st.info("Cotações são buscadas automaticamente (USD, EUR, BTC, ETH → BRL).")

    if "Usuários (Admin)" in tabs:
        with cur[idx]; idx += 1
            if not admin:
                st.warning("Apenas administradores.")
            else:
                st.header("👥 Usuários")
                df = read_df("users")
                st.dataframe(df)
                st.subheader("Criar/Atualizar usuário")
                with st.form("form_user"):
                    u = st.text_input("username (login)")
                    nm = st.text_input("Nome completo")
                    em = st.text_input("Email")
                    pw = st.text_input("Senha inicial/temporária", type="password")
                    col1,col2,col3 = st.columns(3)
                    with col1:
                        is_adm = st.checkbox("Administrador?")
                        c1 = st.checkbox("Pode Notícias")
                        c2 = st.checkbox("Pode Previsão")
                    with col2:
                        c3 = st.checkbox("Pode Aniversários")
                        c4 = st.checkbox("Pode Vídeos")
                    with col3:
                        c5 = st.checkbox("Pode Horas")
                        c6 = st.checkbox("Pode Moedas")
                    if st.form_submit_button("Salvar usuário"):
                        perms = {"can_news":c1,"can_weather":c2,"can_birthdays":c3,"can_videos":c4,"can_worldclocks":c5,"can_currencies":c6}
                        create_user(u, nm, em, pw, is_adm, perms)
                        st.success("Usuário salvo.")
                st.subheader("Alterar minha senha")
                with st.form("form_pw"):
                    newpw = st.text_input("Nova senha", type="password")
                    if st.form_submit_button("Alterar"):
                        if set_password(username, newpw):
                            st.success("Senha alterada.")
                        else:
                            st.error("Falha ao alterar senha.")
