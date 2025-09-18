import time
import pandas as pd
import streamlit as st
from utils.sheets import read_df
from utils.data import fetch_weather, fetch_rates, world_times, get_rotation_index
from utils.ui import inject_base_css, news_card, bday_card, clocks_block, weather_ticker

st.set_page_config(page_title="Lukma TV", page_icon="📺", layout="wide")
inject_base_css()

# botão/ícone para login (painel)
st.markdown("<a class='logo-btn' href='/1_Admin' target='_self'>⚙️ Admin</a>", unsafe_allow_html=True)

# ROTINAS DE DADOS
news_df = read_df("news")
news_df = news_df[news_df["active"].astype(str).str.lower().isin(["true","1","yes"])]
bd_df = read_df("birthdays")
bd_df = bd_df[bd_df["active"].astype(str).str.lower().isin(["true","1","yes"])]
vid_df = read_df("videos")
vid_df = vid_df[vid_df["active"].astype(str).str.lower().isin(["true","1","yes"])]
wu_df = read_df("weather_units")
wu_df = wu_df[wu_df["active"].astype(str).str.lower().isin(["true","1","yes"])]
wc_df = read_df("worldclocks")

# WEATHER & RATES (cacheados)
weather_df = fetch_weather(wu_df)
rates = fetch_rates()
times = world_times()

# ÍNDICES DE ROTAÇÃO
news_interval = int(st.secrets["app"].get("news_rotation_seconds", 10)) * 1000
news_i = get_rotation_index("news", len(news_df), news_interval)
bday_i = get_rotation_index("bdays", len(bd_df), news_interval)
# vídeos usam duração por item; definimos um default de 30s
vid_default_ms = 30_000
if len(vid_df) > 0:
    current_vid = vid_df.iloc[st.session_state.get("rot_videos", 0) % len(vid_df)]
    vid_ms = int(float(current_vid.get("duration_seconds") or 30)) * 1000
else:
    current_vid = None
    vid_ms = vid_default_ms

# REFRESHES (cada área pode pedir)
st_autorefresh_news = st.experimental_rerun  # placeholder
st.autorefresh = st.experimental_rerun       # compat

# Layout em GRID
st.markdown("<div class='grid'>", unsafe_allow_html=True)

# A - Notícias
st.markdown("<div class='a'>", unsafe_allow_html=True)
if len(news_df) == 0:
    st.info("Sem notícias ativas.")
else:
    r = news_df.iloc[news_i % len(news_df)]
    news_card(r["title"], r["description"], r["image_url"])
st.markdown("</div>", unsafe_allow_html=True)

# C - Aniversariantes
st.markdown("<div class='c'>", unsafe_allow_html=True)
if len(bd_df) == 0:
    st.info("Sem aniversariantes cadastrados.")
else:
    r = bd_df.iloc[bday_i % len(bd_df)]
    # dia: aceita "YYYY-MM-DD" -> pegamos apenas o dia
    day = str(r["birthday"])[-2:]
    bday_card(r["name"], r["sector"], day, r["photo_url"])
st.markdown("</div>", unsafe_allow_html=True)

# D - Vídeos
st.markdown("<div class='d'>", unsafe_allow_html=True)
st.markdown("<div class='title'>🎬 Vídeos institucionais</div>", unsafe_allow_html=True)
if current_vid is None:
    st.info("Sem vídeos.")
else:
    url = str(current_vid["url"])
    # Se YouTube, forçar mute+autoplay
    if "youtube.com" in url or "youtu.be" in url:
        if "?" in url: url += "&autoplay=1&mute=1"
        else: url += "?autoplay=1&mute=1"
        st.video(url)
    elif url.lower().endswith((".mp4",".webm",".ogg")):
        st.markdown(f"""
            <video src="{url}" autoplay muted playsinline style="width:100%;border-radius:12px;" />
        """, unsafe_allow_html=True)
    else:
        st.video(url)
st.markdown("</div>", unsafe_allow_html=True)

# E - Horas + Moedas
st.markdown("<div class='e'>", unsafe_allow_html=True)
clocks_block(times, rates)
st.markdown("</div>", unsafe_allow_html=True)

# F - Ticker (Previsão do Tempo)
st.markdown("<div class='f'>", unsafe_allow_html=True)
weather_ticker(weather_df)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# AUTOREFRESH coordenado: notícias 10s; vídeos conforme duração
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit_autorefresh import st_autorefresh as auto  # se não quiser extra dep, substitua por st.experimental_rerun timer

# Implemento simples sem lib externa:
st.markdown(f"""
<script>
setTimeout(function(){{ window.location.reload(); }}, {min(news_interval, vid_ms)});
</script>
""", unsafe_allow_html=True)

# Atualizar índices no próximo ciclo
st.session_state["rot_news"] = (st.session_state.get("rot_news",0)+1) % max(len(news_df),1)
st.session_state["rot_bdays"] = (st.session_state.get("rot_bdays",0)+1) % max(len(bd_df),1)
st.session_state["rot_videos"] = (st.session_state.get("rot_videos",0)+1) % max(len(vid_df),1)
