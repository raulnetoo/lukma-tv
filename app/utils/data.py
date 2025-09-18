import requests
import pandas as pd
import streamlit as st

@st.cache_data(ttl=900, show_spinner=False)  # 15 min
def fetch_weather(units_df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna DF com alias, temperature, windspeed, weathercode.
    Defensivo: funciona se units_df estiver vazio/sem 'active'.
    """
    cols = ["alias","temperature","windspeed","weathercode"]
    if units_df is None or units_df.empty:
        return pd.DataFrame(columns=cols)

    units_df = units_df.copy()
    units_df.columns = [str(c).strip() for c in units_df.columns]
    if "active" in units_df.columns:
        units_df = units_df[units_df["active"].astype(str).str.lower().isin(["true","1","yes"])]

    if units_df.empty:
        return pd.DataFrame(columns=cols)

    rows = []
    for _, r in units_df.iterrows():
        lat = r.get("latitude"); lon = r.get("longitude")
        city = r.get("city")
        alias = r.get("alias") or city or "Unidade"
        try:
            if (not lat or not lon) and city:
                g = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city, "count": 1, "language": "pt"},
                    timeout=10
                ).json()
                if g.get("results"):
                    lat = g["results"][0]["latitude"]; lon = g["results"][0]["longitude"]
            if not lat or not lon:
                continue
            w = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": lat, "longitude": lon, "current_weather": True, "timezone": "America/Sao_Paulo"},
                timeout=10
            ).json()
            cur = w.get("current_weather") or {}
            rows.append({
                "alias": alias,
                "temperature": cur.get("temperature"),
                "windspeed": cur.get("windspeed"),
                "weathercode": cur.get("weathercode"),
            })
        except Exception:
            continue

    return pd.DataFrame(rows, columns=cols)

def weather_emoji(code: int) -> str:
    try:
        code = int(code)
    except Exception:
        return "🌡️"
    if code in [0]: return "☀️"
    if code in [1,2,3]: return "⛅"
    if code in [45,48]: return "🌫️"
    if code in [51,53,55,61,63,65,80,81,82]: return "🌧️"
    if code in [71,73,75,85,86]: return "❄️"
    if code in [95,96,99]: return "⛈️"
    return "🌡️"

@st.cache_data(ttl=300, show_spinner=False)  # 5 min
def fetch_rates() -> dict:
    out = {}
    try:
        f = requests.get("https://api.exchangerate.host/latest", params={"base":"USD","symbols":"BRL"}, timeout=10).json()
        out["USD"] = f["rates"]["BRL"]
    except Exception:
        pass
    try:
        f = requests.get("https://api.exchangerate.host/latest", params={"base":"EUR","symbols":"BRL"}, timeout=10).json()
        out["EUR"] = f["rates"]["BRL"]
    except Exception:
        pass
    try:
        cg = requests.get("https://api.coingecko.com/api/v3/simple/price",
                          params={"ids":"bitcoin,ethereum","vs_currencies":"brl"},
                          timeout=10).json()
        out["BTC"] = cg.get("bitcoin",{}).get("brl")
        out["ETH"] = cg.get("ethereum",{}).get("brl")
    except Exception:
        pass
    return out

def world_times():
    zones = [
        ("Brasília", "America/Sao_Paulo"),
        ("New York", "America/New_York"),
        ("Hong Kong", "Asia/Hong_Kong"),
    ]
    now = pd.Timestamp.utcnow()
    res = []
    for label, z in zones:
        try:
            res.append((label, now.tz_localize("UTC").tz_convert(z).strftime("%H:%M:%S")))
        except Exception:
            res.append((label, "--:--:--"))
    return res

def get_rotation_index(key: str, total: int, default_interval_ms: int) -> int:
    if total <= 0:
        return 0
    idx_key = f"rot_{key}"
    st.session_state[idx_key] = (st.session_state.get(idx_key, 0)) % total
    return st.session_state[idx_key]
