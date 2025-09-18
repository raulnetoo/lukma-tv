from app.utils.data import get_rotation_index

def test_rotation_wraps(monkeypatch):
    class SS(dict): pass
    import streamlit as st
    st.session_state = SS()
    idx = get_rotation_index("news", total=3, default_interval_ms=1000)
    assert idx == 0
