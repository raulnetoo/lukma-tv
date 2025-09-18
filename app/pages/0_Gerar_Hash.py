import secrets
import hashlib
import streamlit as st

st.set_page_config(page_title="Gerar Hash de Senha", layout="centered")
st.header("🔐 Gerar password_salt e password_hash (SHA-256)")

password = st.text_input("Senha", type="password")
if st.button("Gerar"):
    if not password:
        st.error("Informe uma senha.")
    else:
        salt = secrets.token_hex(16)
        pwhash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        st.success("Gerados com sucesso! Copie e cole na planilha (aba 'users').")
        st.code(f"password_salt = {salt}", language="bash")
        st.code(f"password_hash = {pwhash}", language="bash")
        st.info("⚠️ Guarde o salt/hash com segurança. Você pode apagar esta página depois de criar o usuário.")
