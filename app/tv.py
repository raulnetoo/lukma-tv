import pandas as pd
import streamlit as st

from utils.sheets import read_tables
from utils.data import fetch_weather, fetch_rates, world_times
from utils.ui import (
    inject_base_css,
    news_card,
    bday_card,
    weather_ticker,
    video_player,     # << nome correto
    line_e_block,     # << nome correto
)

# ------------------------------ Config & CSS ------------------------------
st.set_page_config(page_title="Lukma TV", page_icon="📺", layout="wide")
inject_base_css()
st.markdown("<a class='logo-btn' href='/1_Admin' target='_self'>⚙️ Admin</a>", unsafe_allow_html=True)

# ------------------------------ Dados ------------------------------
TABLES = ["news","birthdays","videos","weather_units","worldclocks"]
tables = read_tables(TABLES)

def filter_active(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    df = df.copy(); df.columns = [str(c).strip() for c in df.columns]
    if "active" in df.columns:
        df = df[df["active"].astype(str).str.lower().isin(["true","1","yes"])]
    return df.reset_index(drop=True)

def safe_len(df: pd.DataFrame) -> int:
    return 0 if df is None or df.empty else len(df)

news_df = filter_active(tables.get("news", pd.DataFrame()))
bd_df   = filter_active(tables.get("birthdays", pd.DataFrame()))
vid_df  = filter_active(tables.get("videos", pd.DataFrame()))

wu_df_raw = tables.get("weather_units", pd.DataFrame())
wu_df = filter_active(wu_df_raw) if not wu_df_raw.empty else pd.DataFrame()
wc_df = tables.get("worldclocks", pd.DataFrame())

weather_df = fetch_weather(wu_df if not wu_df.empty else pd.DataFrame())
rates = fetch_rates()
times = world_times()

# rotação (notícia, aniversariante, vídeo)
news_interval_ms = int(st.secrets["app"].get("news_rotation_seconds", 10)) * 1000
news_i = st.session_state.get("rot_news", 0) % max(safe_len(news_df), 1)
bday_i = st.session_state.get("rot_bdays", 0) % max(safe_len(bd_df), 1)

vid_default_ms = 30_000
if safe_len(vid_df) > 0:
    current_vid = vid_df.iloc[st.session_state.get("rot_videos", 0) % len(vid_df)]
    try:
        vid_ms = int(float(current_vid.get("duration_seconds") or 30)) * 1000
    except Exception:
        vid_ms = vid_default_ms
else:
    current_vid = None
    vid_ms = vid_default_ms

# ------------------------------ GRID ------------------------------
st.markdown("<div class='grid'>", unsafe_allow_html=True)

# A - Notícias
st.markdown("<div class='area a'>", unsafe_allow_html=True)
if safe_len(news_df) == 0:
    st.markdown("<div class='title'>📰 Notícias</div><div class='empty'>Sem notícias ativas.</div>", unsafe_allow_html=True)
else:
    r = news_df.iloc[news_i]
    news_card(r.get("title",""), r.get("description",""), r.get("image_url",""))
st.markdown("</div>", unsafe_allow_html=True)

# C - Aniversariantes
st.markdown("<div class='area c'>", unsafe_allow_html=True)
if safe_len(bd_df) == 0:
    st.markdown("<div class='title'>🎉 Aniversariante do mês</div><div class='empty'>Sem aniversariantes.</div>", unsafe_allow_html=True)
else:
    r = bd_df.iloc[bday_i]
    day = str(r.get("birthday",""))[-2:] if r.get("birthday") else "--"
    bday_card(r.get("name",""), r.get("sector",""), day, r.get("photo_url",""))
st.markdown("</div>", unsafe_allow_html=True)

# D - Vídeos
st.markdown("<div class='area d'>", unsafe_allow_html=True)
if current_vid is None:
    st.markdown("<div class='title'>🎬 Vídeos institucionais</div><div class='empty'>Sem vídeos.</div>", unsafe_allow_html=True)
else:
    video_player(str(current_vid.get("url","")))
st.markdown("</div>", unsafe_allow_html=True)

# E - 3 cartões: Câmbio | Horários | Clima (1ª unidade)
st.markdown("<div class='area e'>", unsafe_allow_html=True)
line_e_block(times, rates, weather_df if weather_df is not None else pd.DataFrame())
st.markdown("</div>", unsafe_allow_html=True)

# F - Ticker (tempo)
st.markdown("<div class='area f'>", unsafe_allow_html=True)
weather_ticker(weather_df if weather_df is not None else pd.DataFrame())
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------ Auto refresh + índices ------------------------------
refresh_ms = min(news_interval_ms, vid_ms)
st.markdown(f"<script>setTimeout(function(){{ window.location.reload(); }}, {refresh_ms});</script>", unsafe_allow_html=True)
st.session_state["rot_news"]   = (st.session_state.get("rot_news", 0) + 1) % max(safe_len(news_df), 1)
st.session_state["rot_bdays"]  = (st.session_state.get("rot_bdays", 0) + 1) % max(safe_len(bd_df), 1)
st.session_state["rot_videos"] = (st.session_state.get("rot_videos", 0) + 1) % max(safe_len(vid_df), 1)
