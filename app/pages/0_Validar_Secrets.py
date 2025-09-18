import streamlit as st

st.set_page_config(page_title="Validador de Secrets", layout="centered")

pk = st.secrets["gcp_service_account"].get("private_key", "")
st.write("Começo:", pk[:40].replace("\n", "\\n"), "...")
st.write("Termina:", pk[-40:].replace("\n","\\n"))

ok = pk.strip().startswith("-----BEGIN PRIVATE KEY-----") and pk.strip().endswith("-----END PRIVATE KEY-----")
st.write("Formato header/footer OK?", ok)

st.write("Contém quebras (\\n ou reais)?", ("\\n" in pk) or ("\n" in pk))

if not ok:
    st.error("Header/rodapé inválidos. Reveja a formatação conforme ‘Opção A’ ou ‘Opção B’.")
else:
    st.success("Header/rodapé parecem corretos. Se ainda falhar, verifique se não há caracteres estranhos.")
