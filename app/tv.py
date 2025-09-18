import pandas as pd
import streamlit as st

from utils.sheets import read_tables
from utils.data import fetch_weather, fetch_rates, world_times
from utils.ui import inject_base_css, news_card, bday_card, clocks_block, weather_ticker

# --------------------------------- Config & CSS ---------------------------------
st.set_page_config(page_title="Lukma TV", page_icon="📺", layout="wide")
inject_base_css()

# botão/ícone para login (painel)
st.markdown("<a class='logo-btn' href='/1_Admin' target='_self'>⚙️ Admin</a>", unsafe_allow_html=True)

# ------------------------------ Leitura EM LOTE ---------------------------------
TABLES = ["news","birthdays","videos","weather_units","worldclocks"]
tables = read_tables(TABLES)  # UMA chamada ao Sheets (cacheada por 120s)

def filter_active(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if "active" in df.columns:
        df = df[df["active"].astype(str).str.lower().isin(["true","1","yes"])]
    return df.reset_index(drop=True)

news_df = filter_active(tables.get("news"))
bd_df   = filter_active(tables.get("birthdays"))
vid_df  = filter_active(tables.get("videos"))

wu_df_raw = tables.get("weather_units") or pd.DataFrame()
wu_df_raw.columns = [str(c).strip() for c in wu_df_raw.columns]
wu_df = filter_active(wu_df_raw) if not wu_df_raw.empty else pd.DataFrame()

wc_df = tables.get("worldclocks") or pd.DataFrame()

# WEATHER & RATES (cacheados)
weather_df = fetch_weather(wu_df if not wu_df.empty else pd.DataFrame())
rates = fetch_rates()
times = world_times()

# -------------------------- Índices de rotação / refresh ------------------------
news_interval_ms = int(st.secrets["app"].get("news_rotation_seconds", 10)) * 1000
def safe_len(df: pd.DataFrame) -> int:
    return 0 if df is None or df.empty else len(df)

news_i = st.session_state.get("rot_news", 0) % max(safe_len(news_df), 1)
bday_i = st.session_state.get("rot_bdays", 0) % max(safe_len(bd_df), 1)

# vídeos: duração por item; default 30s
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

# --------------------------------- Layout em GRID --------------------------------
st.markdown("<div class='grid'>", unsafe_allow_html=True)

# A - Notícias
st.markdown("<div class='a'>", unsafe_allow_html=True)
if safe_len(news_df) == 0:
    st.info("Sem notícias ativas ou cabeçalho ausente na aba 'news'.")
else:
    r = news_df.iloc[news_i]
    news_card(r.get("title",""), r.get("description",""), r.get("image_url",""))
st.markdown("</div>", unsafe_allow_html=True)

# C - Aniversariantes
st.markdown("<div class='c'>", unsafe_allow_html=True)
if safe_len(bd_df) == 0:
    st.info("Sem aniversariantes (ou cabeçalho ausente em 'birthdays').")
else:
    r = bd_df.iloc[bday_i]
    day = str(r.get("birthday",""))[-2:] if r.get("birthday") else "--"
    bday_card(r.get("name",""), r.get("sector",""), day, r.get("photo_url",""))
st.markdown("</div>", unsafe_allow_html=True)

# D - Vídeos
st.markdown("<div class='d'>", unsafe_allow_html=True)
st.markdown("<div class='title'>🎬 Vídeos institucionais</div>", unsafe_allow_html=True)
if current_vid is None:
    st.info("Sem vídeos.")
else:
    url = str(current_vid.get("url", ""))
    if "youtube.com" in url or "youtu.be" in url:
        url = url + ("&" if "?" in url else "?") + "autoplay=1&mute=1"
        st.video(url)
    elif url.lower().endswith((".mp4",".webm",".ogg")):
        st.markdown(
            f"""<video src="{url}" autoplay muted playsinline style="width:100%;border-radius:12px;" />""",
            unsafe_allow_html=True
        )
    else:
        st.video(url)
st.markdown("</div>", unsafe_allow_html=True)

# E - Horas + Moedas
st.markdown("<div class='e'>", unsafe_allow_html=True)
clocks_block(times, rates)
st.markdown("</div>", unsafe_allow_html=True)

# F - Ticker (Previsão do Tempo)
st.markdown("<div class='f'>", unsafe_allow_html=True)
weather_ticker(weather_df if weather_df is not None else pd.DataFrame())
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------- Auto refresh ----------------------------------
refresh_ms = min(news_interval_ms, vid_ms)
st.markdown(
    f"<script>setTimeout(function(){{ window.location.reload(); }}, {refresh_ms});</script>",
    unsafe_allow_html=True
)

# Atualiza índices para o próximo ciclo
st.session_state["rot_news"]   = (st.session_state.get("rot_news", 0) + 1) % max(safe_len(news_df), 1)
st.session_state["rot_bdays"]  = (st.session_state.get("rot_bdays", 0) + 1) % max(safe_len(bd_df), 1)
st.session_state["rot_videos"] = (st.session_state.get("rot_videos", 0) + 1) % max(safe_len(vid_df), 1)
