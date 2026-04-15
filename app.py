import streamlit as st
from datetime import date
import pandas as pd

st.set_page_config(page_title="Análise de Jogos", layout="centered")

st.title("📊 Análise de Jogos")
st.caption("Painel simples para estudar os jogos do dia")

data_escolhida = st.date_input("Escolha a data dos jogos", value=date.today())

competicoes = st.multiselect(
    "Filtrar competições",
    ["Champions League", "Libertadores", "Sul-Americana", "U.S. Open Cup", "CONCACAF Champions Cup"],
    default=["Champions League", "Libertadores", "Sul-Americana", "U.S. Open Cup", "CONCACAF Champions Cup"],
)

if st.button("Analisar agora"):
    dados = [
        {
            "Horário": "15/04 16:00",
            "Competição": "Champions League",
            "Jogo": "Arsenal x Sporting",
            "Tendência": "Leve vantagem do mandante",
            "Gols": "Tendência moderada de gols",
            "Risco": "Médio",
            "Confiança": "63%",
        },
        {
            "Horário": "15/04 16:00",
            "Competição": "Champions League",
            "Jogo": "Bayern x Real Madrid",
            "Tendência": "Jogo equilibrado",
            "Gols": "Tendência de gols",
            "Risco": "Alto",
            "Confiança": "54%",
        },
        {
            "Horário": "15/04 21:30",
            "Competição": "Libertadores",
            "Jogo": "Cruzeiro x Universidad Católica",
            "Tendência": "Mandante mais forte",
            "Gols": "Tendência moderada de gols",
            "Risco": "Baixo",
            "Confiança": "74%",
        },
        {
            "Horário": "15/04 19:00",
            "Competição": "Sul-Americana",
            "Jogo": "Racing x Botafogo",
            "Tendência": "Jogo equilibrado",
            "Gols": "Tendência de poucos gols",
            "Risco": "Alto",
            "Confiança": "54%",
        },
        {
            "Horário": "15/04 20:30",
            "Competição": "U.S. Open Cup",
            "Jogo": "Columbus Crew x Richmond Kickers",
            "Tendência": "Mandante mais forte",
            "Gols": "Tendência de gols",
            "Risco": "Baixo",
            "Confiança": "74%",
        },
        {
            "Horário": "15/04 23:00",
            "Competição": "CONCACAF Champions Cup",
            "Jogo": "Seattle Sounders x Tigres",
            "Tendência": "Jogo equilibrado",
            "Gols": "Tendência moderada de gols",
            "Risco": "Médio",
            "Confiança": "63%",
        },
    ]

    df = pd.DataFrame(dados)
    df = df[df["Competição"].isin(competicoes)]

    st.success(f"Análise gerada para {data_escolhida}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Jogos", len(df))
    c2.metric("Risco baixo", (df["Risco"] == "Baixo").sum())
    c3.metric("Risco alto", (df["Risco"] == "Alto").sum())

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar CSV",
        data=csv,
        file_name="analise_jogos.csv",
        mime="text/csv",
        use_container_width=True,
    )
