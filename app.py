import streamlit as st
from datetime import date

st.set_page_config(page_title="Análise de Jogos", layout="centered")

st.title("📊 Análise de Jogos")

st.write("Sistema online funcionando 🚀")

data = st.date_input("Escolha a data dos jogos", value=date.today())

if st.button("Analisar agora"):
    st.success(f"Analisando jogos do dia: {data}")
    st.info("Próximo passo: vamos ativar análise automática 🔥")
