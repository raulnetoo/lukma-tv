import streamlit as st
from .data import weather_emoji

def inject_base_css():
    st.markdown("""
    <style>
      body { background: #0b1220; color: #e5e7eb; }
      .grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        grid-template-rows: repeat(4, 22vh) 8vh;
        gap: 10px;
        padding: 10px;
      }
      .a { grid-column: 1 / span 3; grid-row: 1 / span 2; background: #0f172a; border-radius: 16px; padding: 16px; }
      .c { grid-column: 1 / span 3; grid-row: 3 / span 2; background: #0f172a; border-radius: 16px; padding: 16px; }
      .d { grid-column: 4 / span 5; grid-row: 1 / span 3; background: #0f172a; border-radius: 16px; padding: 16px; }
      .e { grid-column: 4 / span 5; grid-row: 4 / span 1; background: #0f172a; border-radius: 16px; padding: 16px; }
      .f { grid-column: 1 / span 8; grid-row: 5 / span 1; background: #111827; border-radius: 12px; padding: 6px 0; overflow: hidden; }
      .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 12px; }
      .title { color: #60a5fa; font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; }
      .news-img { width: 100%; height: 36vh; object-fit: cover; border-radius: 12px; }
      .ticker {
        white-space: nowrap; display: inline-block; 
        animation: marquee 30s linear infinite;
        font-size: 1.1rem;
      }
      @keyframes marquee { 0% { transform: translateX(100%);} 100% { transform: translateX(-100%);} }
      .rates { margin-top: 8px; font-size: .95rem; color: #93c5fd; }
      .logo-btn { position: fixed; top: 8px; right: 12px; background: #1f2937; padding: 8px 12px; border-radius: 999px; }
      .badge { background:#1d4ed8; color:white; border-radius:8px; padding:2px 8px; margin-right:6px; }
    </style>
    """, unsafe_allow_html=True)

def news_card(title, desc, img_url):
    st.markdown(f"""
      <div class='card'>
        <div class='title'>📰 Notícias</div>
        <img src="{img_url}" class="news-img" alt="Imagem da notícia" />
        <h3 style="margin:8px 0 4px 0;">{title}</h3>
        <p style="color:#cbd5e1;">{desc}</p>
      </div>
    """, unsafe_allow_html=True)

def bday_card(name, sector, day, photo_url):
    st.markdown(f"""
      <div class='card'>
        <div class='title'>🎉 Aniversariante do mês</div>
        <div style="display:flex; gap:16px; align-items:center;">
          <img src="{photo_url}" alt="Foto" style="width:120px;height:120px;border-radius:16px;object-fit:cover;border:2px solid #1f2937;" />
          <div>
            <div style="font-size:1.4rem;font-weight:800;">{name}</div>
            <div style="color:#93c5fd;">{sector}</div>
            <div style="margin-top:6px;"><span class="badge">Dia {day}</span></div>
            <img src="https://media.tenor.com/xaGx2Y0lqJAAAAAC/confetti-celebrate.gif" alt="confetti" style="height:60px;margin-top:6px;" />
          </div>
        </div>
      </div>
    """, unsafe_allow_html=True)

def clocks_block(times, rates: dict):
    html_rates = ""
    if rates:
        html_rates = " · ".join([f"<span class='badge'>{k}=R$ {v:,.2f}</span>" for k,v in rates.items() if v])
    items = "".join([f"<div class='card'><div style='font-size:1.2rem;font-weight:700;'>{lbl}</div><div style='font-size:2rem'>{hhmmss}</div></div>" for lbl, hhmmss in times])
    st.markdown(f"""
    <div class='title'>🕒 Horas mundiais</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">{items}</div>
    <div class="rates">💱 Cotações: {html_rates}</div>
    """, unsafe_allow_html=True)

def weather_ticker(df):
    if df.empty:
        st.markdown("<div class='ticker'>Sem dados de tempo...</div>", unsafe_allow_html=True); return
    parts = []
    for _, r in df.iterrows():
        emo = weather_emoji(int(r.get("weathercode") or 0))
        parts.append(f"<span class='badge'>{r['alias']}</span> {r['temperature']}°C {emo}")
    st.markdown(f"<div class='ticker'>{' · '.join(parts)} · {' · '.join(parts)}</div>", unsafe_allow_html=True)
