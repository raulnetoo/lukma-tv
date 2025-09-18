import math
import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple

def inject_base_css():
    st.markdown(
        """
        <style>
        :root{
          --bg:#0b1220;
          --card:#111827;
          --muted:#9CA3AF;
          --text:#F9FAFB;
          --blue:#2563eb;
          --green:#10b981;
          --pink:#ec4899;
          --yellow:#f59e0b;
          --red:#ef4444;
          --shadow: 0 10px 30px rgba(0,0,0,.25);
          --radius: 16px;
        }
        html, body, [data-testid="stAppViewContainer"]{
          background: radial-gradient(1200px 600px at 10% 10%, #0f172a 10%, #0b1220 60%, #0b1220 100%) fixed;
          color: var(--text);
        }
        /* remove paddings laterais do Streamlit */
        [data-testid="stAppViewBlockContainer"]{padding-top: 1rem; padding-bottom: 0;}

        /* Botão/ícone do Admin (canto superior esquerdo) */
        .logo-btn{
          position: fixed; top: 12px; left: 16px; z-index: 9999;
          background: #0f172a; border: 1px solid #1f2937; color: #e5e7eb;
          padding: 8px 12px; border-radius: 999px; text-decoration: none; box-shadow: var(--shadow);
          transition: transform .15s ease, background .2s ease, border-color .2s ease;
          font-weight: 600;
        }
        .logo-btn:hover{ transform: translateY(-2px); background:#111827; border-color:#374151; }

        /* GRID principal
           Layout desejado:
           aaadddd
           aaadddd
           cccdddd
           ccceeee
           fffffff  (ticker)
        */
        .grid{
          display: grid;
          grid-template-columns: repeat(8, 1fr);
          grid-template-rows: auto auto auto auto 66px;
          grid-template-areas:
            "a a a d d d d d"
            "a a a d d d d d"
            "c c c d d d d d"
            "c c c e e e e e"
            "f f f f f f f f";
          gap: 16px;
          padding: 56px 16px 12px 16px; /* espaço pro botão admin */
        }
        .grid > .a, .grid > .c, .grid > .d, .grid > .e{
          background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: var(--radius);
          box-shadow: var(--shadow);
          overflow: hidden;
          position: relative;
        }
        .grid > .a{ grid-area: a; min-height: 360px; }
        .grid > .c{ grid-area: c; min-height: 280px; }
        .grid > .d{ grid-area: d; min-height: 520px; }
        .grid > .e{ grid-area: e; min-height: 220px; }

        .grid > .f{
          grid-area: f; height: 66px;
          background: #0a1629; border: 1px solid rgba(255,255,255,0.06);
          border-radius: var(--radius);
          box-shadow: var(--shadow); overflow: hidden; position: relative;
        }

        /* Títulos internos */
        .title{
          font-weight: 700; letter-spacing: .3px; color:#e5e7eb;
          border-bottom: 1px dashed rgba(255,255,255,0.08);
          padding: 10px 14px; background: rgba(255,255,255,0.02);
        }

        /* Card padrões */
        .card{
          padding: 14px; display: flex; gap: 14px; align-items: stretch;
        }
        .media{
          width: 38%; min-height: 200px; border-radius: 12px; overflow: hidden; background:#0b1324; border:1px solid rgba(255,255,255,0.06)
        }
        .media img{ width: 100%; height: 100%; object-fit: cover; display:block; }
        .content{ width: 62%; display:flex; flex-direction: column; gap: 8px; }
        .content h2{ margin:0; font-size: 1.5rem; }
        .content p{ margin:0; color: var(--muted); }

        /* B-day card */
        .bday{
          display:flex; gap:16px; align-items:center; padding:14px; position:relative;
        }
        .bday .photo{
          width:120px; height:120px; border-radius: 14px; overflow:hidden;
          background:#0b1324; border:1px solid rgba(255,255,255,0.06)
        }
        .bday .photo img{ width:100%; height:100%; object-fit: cover; display:block; }
        .bday .info{ display:flex; flex-direction:column; gap:6px; }
        .bday .name{ font-size:1.6rem; font-weight:800; }
        .badge{
          display:inline-block; padding:4px 10px; border-radius:999px;
          background: rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.35); color:#a7f3d0; font-weight:700; font-size:.9rem;
        }
        .day-badge{
          display:inline-block; padding:4px 10px; border-radius:999px;
          background: rgba(59,130,246,.12); border:1px solid rgba(59,130,246,.35); color:#bfdbfe; font-weight:700; font-size:.9rem; margin-left:6px;
        }

        /* Confete leve em CSS */
        .confetti-container { position:absolute; inset:0; pointer-events:none; overflow:hidden; }
        .confetti {
          position:absolute; top:-10px; width:8px; height:12px; opacity:.85; border-radius:2px;
          animation: fall linear forwards;
        }
        @keyframes fall {
          to { transform: translateY(160%); opacity: .9; }
        }

        /* Clocks & Rates */
        .row{ display:flex; gap:16px; padding: 10px 14px; }
        .chip{
          background: #0a1629; border:1px solid rgba(255,255,255,0.08); border-radius: 12px;
          padding:10px 14px; display:flex; align-items:center; gap:10px;
          box-shadow: var(--shadow);
        }
        .chip .lbl{ color:#9ca3af; font-weight:700; }
        .chip .val{ font-weight:800; letter-spacing:.3px; }

        /* Weather ticker (marquee) */
        .ticker-wrap{ position:relative; width:100%; height:66px; overflow:hidden; }
        .ticker{
          position:absolute; white-space: nowrap; will-change: transform;
          animation: scroll-left 28s linear infinite;
        }
        @keyframes scroll-left {
          0% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
        .tick-item{
          display:inline-flex; align-items:center; gap:8px; margin: 0 18px;
          padding: 8px 12px; border-radius: 999px; background: #0f172a; border:1px solid rgba(255,255,255,0.08);
        }
        .tick-emoji{ font-size: 1.1rem; }
        .tick-val{ font-weight:800; }

        /* Responsivo */
        @media (max-width: 1100px){
          .media{ width: 44%; }
          .content{ width: 56%; }
        }
        @media (max-width: 900px){
          .grid{
            grid-template-columns: 1fr;
            grid-template-rows: auto;
            grid-template-areas:
              "a"
              "c"
              "d"
              "e"
              "f";
          }
          .media{ width:100%; min-height:180px; }
          .content{ width:100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _confetti_html(n=24):
    # gera N pedaços com cores aleatórias CSS (pré-definidas para evitar JS)
    colors = ["#f59e0b", "#10b981", "#3b82f6", "#ef4444", "#eab308", "#a855f7", "#22d3ee", "#84cc16", "#f97316"]
    pieces = []
    for i in range(n):
        left = f"{(i * (100/n)) + 1:.2f}%"
        delay = f"{(i%10)*0.12:.2f}s"
        dur = f"{2.8 + (i%5)*0.25:.2f}s"
        color = colors[i % len(colors)]
        xjitter = (-30 + (i*7) % 60)  # apenas variação simples
        pieces.append(
            f"<span class='confetti' style='left:{left}; background:{color}; animation-duration:{dur}; animation-delay:{delay}; transform: translateX({xjitter}px)'></span>"
        )
    return "<div class='confetti-container'>" + "".join(pieces) + "</div>"

def news_card(title: str, description: str, image_url: str):
    st.markdown("<div class='title'>📰 Notícias</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    # imagem
    st.markdown(
        f"""
        <div class='media'>
          <img src="{image_url or 'https://picsum.photos/800/450'}" alt="Imagem da notícia" />
        </div>
        """,
        unsafe_allow_html=True
    )
    # texto
    st.markdown(
        f"""
        <div class='content'>
          <h2>{title or 'Título da notícia'}</h2>
          <p>{description or 'Descrição breve da notícia.'}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

def bday_card(name: str, sector: str, day: str, photo_url: str):
    st.markdown("<div class='title'>🎉 Aniversariante do mês</div>", unsafe_allow_html=True)
    # bloco
    st.markdown("<div class='bday'>", unsafe_allow_html=True)
    st.markdown(_confetti_html(26), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='photo'>
          <img src="{photo_url or 'https://i.imgur.com/9b2WQpN.png'}" alt="Foto do aniversariante" />
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class='info'>
          <div class='name'>{name or 'Colaborador(a)'}</div>
          <div>
            <span class='badge'>{sector or 'Setor'}</span>
            <span class='day-badge'>Dia {day or '--'}</span>
          </div>
          <div style="color:#9ca3af">Muitas felicidades! 🎂🎈</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

def _fmt_rate(v):
    try:
        if v is None: return "--"
        if isinstance(v, (int,float)):
            # BRL com 2 casas
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return str(v)
    except Exception:
        return "--"

def clocks_block(times: List[Tuple[str, str]], rates: Dict[str, float]):
    st.markdown("<div class='title'>🕒 Horas mundiais & 💱 Cotações</div>", unsafe_allow_html=True)
    st.markdown("<div class='row'>", unsafe_allow_html=True)
    # Horas
    if times:
        for label, hhmm in times:
            st.markdown(
                f"<div class='chip'><span class='lbl'>{label}</span> <span class='val'>{hhmm}</span></div>",
                unsafe_allow_html=True
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # Moedas
    st.markdown("<div class='row'>", unsafe_allow_html=True)
    if rates:
        usd = _fmt_rate(rates.get("USD"))
        eur = _fmt_rate(rates.get("EUR"))
        btc = _fmt_rate(rates.get("BTC"))
        eth = _fmt_rate(rates.get("ETH"))
        st.markdown(f"<div class='chip'><span class='lbl'>USD</span> <span class='val'>{usd}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chip'><span class='lbl'>EUR</span> <span class='val'>{eur}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chip'><span class='lbl'>BTC</span> <span class='val'>{btc}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chip'><span class='lbl'>ETH</span> <span class='val'>{eth}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='chip'><span class='lbl'>Cotações</span> <span class='val'>--</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def weather_emoji(code):
    try:
        c = int(code)
    except Exception:
        return "🌡️"
    if c in [0]: return "☀️"
    if c in [1,2,3]: return "⛅"
    if c in [45,48]: return "🌫️"
    if c in [51,53,55,61,63,65,80,81,82]: return "🌧️"
    if c in [71,73,75,85,86]: return "❄️"
    if c in [95,96,99]: return "⛈️"
    return "🌡️"

def weather_ticker(df: pd.DataFrame):
    # Espera colunas: alias, temperature, windspeed, weathercode
    items = []
    if df is None or df.empty:
        items.append("<span class='tick-item'><span class='tick-emoji'>🌡️</span><span class='tick-val'>Sem dados</span></span>")
    else:
        for _, r in df.iterrows():
            emoji = weather_emoji(r.get("weathercode"))
            alias = str(r.get("alias") or "Unidade")
            t = r.get("temperature")
            w = r.get("windspeed")
            t_txt = f"{float(t):.0f}°C" if t is not None and str(t) != "nan" else "--°C"
            w_txt = f"{float(w):.0f} km/h" if w is not None and str(w) != "nan" else "-- km/h"
            items.append(
                f"<span class='tick-item'><span class='tick-emoji'>{emoji}</span><b>{alias}</b> • {t_txt} • {w_txt}</span>"
            )
    html = "<div class='ticker-wrap'><div class='ticker'>" + "".join(items) + "</div></div>"
    st.markdown(html, unsafe_allow_html=True)
