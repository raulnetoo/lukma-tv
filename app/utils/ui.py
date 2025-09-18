import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple

def inject_base_css():
    st.markdown(
        """
        <style>
        :root{
          --bg:#0b1220;
          --card:#0f172a;
          --card-border:#1f2a3a;
          --muted:#9CA3AF;
          --text:#F9FAFB;
          --shadow: 0 10px 30px rgba(0,0,0,.25);
          --radius: 16px;

          /* Tamanhos & proporções */
          --avatar-size: 140px;
          --news-thumb-w: 240px;      /* largura da mini imagem de notícia (topo) */
          --news-thumb-ratio: 1 / 1;  /* quadrada */
          --video-ratio: 16 / 9;
          --video-max-h: 520px;
          --block-pad: 14px;
          --gap: 16px;
          --ticker-h: 72px;
        }

        html, body, [data-testid="stAppViewContainer"]{
          background: radial-gradient(1200px 600px at 10% 10%, #0f172a 10%, #0b1220 60%, #0b1220 100%) fixed;
          color: var(--text);
        }
        [data-testid="stAppViewBlockContainer"]{padding-top: 1rem; padding-bottom: 0;}

        /* Botão Admin */
        .logo-btn{
          position: fixed; top: 12px; left: 16px; z-index: 9999;
          background: var(--card); border: 1px solid var(--card-border); color: #e5e7eb;
          padding: 8px 12px; border-radius: 999px; text-decoration: none; box-shadow: var(--shadow);
          font-weight: 600; transition: transform .15s ease, background .2s ease, border-color .2s ease;
        }
        .logo-btn:hover{ transform: translateY(-2px); background:#111827; border-color:#374151; }

        /* GRID: aaadddd / aaadddd / cccdddd / ccceeee / fffffff */
        .grid{
          display: grid;
          grid-template-columns: repeat(8, 1fr);
          grid-template-rows: auto auto auto auto var(--ticker-h);
          grid-template-areas:
            "a a a d d d d d"
            "a a a d d d d d"
            "c c c d d d d d"
            "c c c e e e e e"
            "f f f f f f f f";
          gap: var(--gap);
          padding: 56px 16px 12px 16px;
        }
        .area{
          background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: var(--radius);
          box-shadow: var(--shadow);
          overflow: hidden; position: relative;
        }
        .a{ grid-area:a; min-height: 420px; }
        .c{ grid-area:c; min-height: 320px; }
        .d{ grid-area:d; min-height: 520px; }
        .e{ grid-area:e; min-height: 220px; }
        .f{ grid-area:f; height: var(--ticker-h); background:#0a1629; }

        .title{
          font-weight: 800; letter-spacing: .3px; color:#e5e7eb;
          border-bottom: 1px dashed rgba(255,255,255,0.08);
          padding: 10px 14px; background: rgba(255,255,255,0.02);
        }
        .empty{ padding: 18px 14px; color: var(--muted); font-style: italic; }

        /* =================== NOTÍCIA (estilo do mock) =================== */
        .news-wrap{ padding: 18px 14px 22px 14px; display:flex; flex-direction:column; align-items:center; gap: 16px; }
        .news-thumb{
          width: var(--news-thumb-w);
          aspect-ratio: var(--news-thumb-ratio);
          border-radius: 12px; overflow:hidden;
          background:#0b1324; border:1px solid rgba(255,255,255,0.08);
        }
        .news-thumb img{ width:100%; height:100%; object-fit: cover; display:block; }
        .news-title{
          font-size: clamp(22px, 2.6vw, 30px);
          font-weight: 900; text-align:center; line-height: 1.2; max-width: 90%;
        }
        .news-desc{
          color: var(--muted);
          text-align:center;
          font-size: clamp(14px, 1.3vw, 18px);
          max-width: 880px;
        }

        /* =================== ANIVERSARIANTE (avatar fixo) =================== */
        .bday{ display:grid; grid-template-columns: var(--avatar-size) 1fr; gap:18px; padding: var(--block-pad); position:relative; }
        .bday .photo{
          width: var(--avatar-size); height: var(--avatar-size);
          border-radius: 14px; overflow:hidden; background:#0b1324; border:1px solid rgba(255,255,255,0.08)
        }
        .bday .photo img{ width:100%; height:100%; object-fit: cover; display:block; }
        .bday .info{ display:flex; flex-direction:column; gap:8px; }
        .bday .name{ font-size: clamp(22px, 2.6vw, 30px); font-weight:800; }
        .badge{
          display:inline-block; padding:4px 10px; border-radius:999px;
          background: rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.35); color:#a7f3d0; font-weight:700; font-size:.95rem;
        }
        .day-badge{
          display:inline-block; padding:4px 10px; border-radius:999px;
          background: rgba(59,130,246,.12); border:1px solid rgba(59,130,246,.35); color:#bfdbfe; font-weight:700; font-size:.95rem; margin-left:6px;
        }

        /* Confete */
        .confetti-container { position:absolute; inset:0; pointer-events:none; overflow:hidden; }
        .confetti { position:absolute; top:-10px; width:8px; height:12px; opacity:.9; border-radius:2px; animation: fall linear forwards; }
        @keyframes fall { to { transform: translateY(160%); opacity: .95; } }

        /* =================== Vídeo 16:9 =================== */
        .video-frame{
          position: relative; width: 100%; aspect-ratio: var(--video-ratio);
          max-height: var(--video-max-h); background: #0b1324;
          border:1px solid rgba(255,255,255,0.08); border-radius: 12px; overflow: hidden;
          margin: 12px 14px 16px 14px;
        }
        .video-frame iframe, .video-frame video{
          position:absolute; inset:0; width:100%; height:100%; display:block; object-fit: cover; border:0;
        }

        /* =================== Linha E: 3 cartões =================== */
        .row3{ display:grid; grid-template-columns: 1fr 1.2fr 1.2fr; gap: var(--gap); padding: 12px 14px 18px 14px; }
        .card-mini{
          background: #0b1324; border:1px solid rgba(255,255,255,0.08);
          border-radius: 12px; padding: 12px 14px; box-shadow: var(--shadow);
        }
        .card-mini .head{ font-weight:800; letter-spacing:.3px; margin-bottom: 8px; }
        .fx-col{ display:flex; flex-direction:column; gap:8px; }
        .chip{ background:#0a1629; border:1px solid rgba(255,255,255,0.10); border-radius: 10px; padding:8px 12px; display:flex; align-items:center; justify-content:space-between; }
        .muted{ color:#9ca3af; }
        .big{ font-size: clamp(18px, 2vw, 22px); font-weight:800; }

        /* Clima mini card (parecido ao do print) */
        .weather-mini{ display:grid; grid-template-columns: auto 1fr; gap: 12px; align-items:center; }
        .weather-emoji{ font-size: 26px; }
        .weather-line{ display:flex; gap:10px; align-items:center; color:#cbd5e1; }
        .weather-temp{ font-weight:900; font-size: 28px; }
        .weather-sub{ font-size: 13px; color:#9ca3af; }

        /* Ticker */
        .ticker-wrap{ position:relative; width:100%; height:100%; overflow:hidden; }
        .ticker{ position:absolute; white-space: nowrap; will-change: transform; animation: scroll-left 28s linear infinite; }
        @keyframes scroll-left { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
        .tick-item{ display:inline-flex; align-items:center; gap:8px; margin: 0 18px; padding: 8px 12px; border-radius: 999px; background: #0f172a; border:1px solid rgba(255,255,255,0.10); }
        .tick-emoji{ font-size: 1.1rem; }
        .tick-val{ font-weight:800; }

        /* Responsivo */
        @media (max-width: 1100px){
          .row3{ grid-template-columns: 1fr; }
        }
        @media (max-width: 900px){
          .grid{
            grid-template-columns: 1fr; grid-template-rows: auto;
            grid-template-areas: "a" "c" "d" "e" "f";
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _confetti_html(n=24):
    colors = ["#f59e0b", "#10b981", "#3b82f6", "#ef4444", "#eab308", "#a855f7", "#22d3ee", "#84cc16", "#f97316"]
    pieces = []
    for i in range(n):
        left = f"{(i * (100/n)) + 1:.2f}%"
        delay = f"{(i%10)*0.12:.2f}s"
        dur = f"{2.8 + (i%5)*0.25:.2f}s"
        color = colors[i % len(colors)]
        xj = (-30 + (i*7) % 60)
        pieces.append(
            f"<span class='confetti' style='left:{left}; background:{color}; animation-duration:{dur}; animation-delay:{delay}; transform: translateX({xj}px)'></span>"
        )
    return "<div class='confetti-container'>" + "".join(pieces) + "</div>"

# ========== Componentes ==========
def news_card(title: str, description: str, image_url: str):
    st.markdown("<div class='title'>📰 Notícias</div>", unsafe_allow_html=True)
    st.markdown("<div class='news-wrap'>", unsafe_allow_html=True)
    st.markdown(
        f"""<div class='news-thumb'><img src="{image_url or 'https://picsum.photos/400'}" alt="Imagem da notícia" /></div>""",
        unsafe_allow_html=True
    )
    st.markdown(f"""<div class='news-title'>{title or 'Título da notícia'}</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class='news-desc'>{description or 'Descrição breve da notícia.'}</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def bday_card(name: str, sector: str, day: str, photo_url: str):
    st.markdown("<div class='title'>🎉 Aniversariante do mês</div>", unsafe_allow_html=True)
    st.markdown("<div class='bday'>", unsafe_allow_html=True)
    st.markdown(_confetti_html(26), unsafe_allow_html=True)
    st.markdown(
        f"""<div class='photo'><img src="{photo_url or 'https://i.imgur.com/9b2WQpN.png'}" alt="Foto do aniversariante" /></div>""",
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class='info'>
          <div class='name'>{name or 'Colaborador(a)'}</div>
          <div><span class='badge'>{sector or 'Setor'}</span><span class='day-badge'>Dia {day or '--'}</span></div>
          <div style="color:#9ca3af">Muitas felicidades! 🎂🎈</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

def _fmt_rate(v):
    try:
        if v is None: return "--"
        if isinstance(v, (int,float)): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return str(v)
    except Exception: return "--"

def weather_emoji(code):
    try: c = int(code)
    except Exception: return "🌡️"
    if c in [0]: return "☀️"
    if c in [1,2,3]: return "⛅"
    if c in [45,48]: return "🌫️"
    if c in [51,53,55,61,63,65,80,81,82]: return "🌧️"
    if c in [71,73,75,85,86]: return "❄️"
    if c in [95,96,99]: return "⛈️"
    return "🌡️"

def weather_ticker(df: pd.DataFrame):
    items = []
    if df is None or df.empty:
        items.append("<span class='tick-item'><span class='tick-emoji'>🌡️</span><span class='tick-val'>Sem dados</span></span>")
    else:
        for _, r in df.iterrows():
            emoji = weather_emoji(r.get("weathercode")); alias = str(r.get("alias") or "Unidade")
            t = r.get("temperature"); w = r.get("windspeed")
            t_txt = f"{float(t):.0f}°C" if t is not None and str(t) != "nan" else "--°C"
            w_txt = f"{float(w):.0f} km/h" if w is not None and str(w) != "nan" else "-- km/h"
            items.append(f"<span class='tick-item'><span class='tick-emoji'>{emoji}</span><b>{alias}</b> • {t_txt} • {w_txt}</span>")
    st.markdown("<div class='ticker-wrap'><div class='ticker'>" + "".join(items) + "</div></div>", unsafe_allow_html=True)

def video_player(url: str):
    st.markdown("<div class='title'>🎬 Vídeos institucionais</div>", unsafe_allow_html=True)
    if not url:
        st.markdown("<div class='empty'>Sem vídeo configurado.</div>", unsafe_allow_html=True); return
    if "youtube.com" in url or "youtu.be" in url:
        yt = url + ("&" if "?" in url else "?") + "autoplay=1&mute=1&playsinline=1&controls=0"
        st.markdown(f"<div class='video-frame'><iframe src='{yt}' allow='autoplay; encrypted-media;'></iframe></div>", unsafe_allow_html=True)
    elif url.lower().endswith((".mp4",".webm",".ogg")):
        st.markdown(f"<div class='video-frame'><video src='{url}' autoplay muted playsinline></video></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='video-frame'><iframe src='{url}'></iframe></div>", unsafe_allow_html=True)

def line_e_block(times: List[Tuple[str, str]], rates: Dict[str, float], weather_df: pd.DataFrame):
    """Renderiza 3 cartões: CÂMBIO | HORÁRIOS | CLIMA (1 unidade)"""
    st.markdown("<div class='row3'>", unsafe_allow_html=True)

    # 1) Câmbio
    usd = _fmt_rate(rates.get("USD")); eur = _fmt_rate(rates.get("EUR"))
    btc = _fmt_rate(rates.get("BTC")); eth = _fmt_rate(rates.get("ETH"))
    st.markdown("<div class='card-mini'><div class='head'>💱 Câmbio</div>", unsafe_allow_html=True)
    st.markdown("<div class='fx-col'>", unsafe_allow_html=True)
    st.markdown(f"<div class='chip'><span class='muted'>1 Dólar</span><span class='big'>{usd}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chip'><span class='muted'>1 Euro</span><span class='big'>{eur}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chip'><span class='muted'>1 BTC</span><span class='big'>{btc}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chip'><span class='muted'>1 ETH</span><span class='big'>{eth}</span></div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # 2) Horários
    st.markdown("<div class='card-mini'><div class='head'>🕒 Horários</div>", unsafe_allow_html=True)
    if times:
        for label, hhmm in times:
            st.markdown(f"<div class='chip'><span class='muted'>{label}</span><span class='big'>{hhmm}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='muted'>Sem horários.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 3) Clima (primeira unidade)
    alias = "Unidade"; temp = "--"; wind = "--"; emoji = "🌡️"
    if weather_df is not None and not weather_df.empty:
        r = weather_df.iloc[0]
        alias = r.get("alias") or alias
        t = r.get("temperature"); w = r.get("windspeed")
        temp = f"{float(t):.0f}°C" if t is not None and str(t) != 'nan' else "--°C"
        wind = f"{float(w):.0f} km/h" if w is not None and str(w) != 'nan' else "-- km/h"
        emoji = weather_emoji(r.get("weathercode"))
    st.markdown("<div class='card-mini'><div class='head'>🌦️ Clima</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='weather-mini'>
          <div class='weather-emoji'>{emoji}</div>
          <div>
            <div class='weather-line'><span class='weather-temp'>{temp}</span> <span class='weather-sub'>{wind}</span></div>
            <div class='muted'>{alias}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
