import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="Análise de Jogos", layout="wide")

st.title("📊 Análise de Jogos")
st.caption("API-Football • jogos do dia com filtros por país e competição")

API_KEY = st.secrets.get("API_FOOTBALL_KEY")

if not API_KEY:
    st.error("Chave não encontrada. Vá em Settings > Secrets e adicione API_FOOTBALL_KEY.")
    st.stop()

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# Países que você quer destacar no app
PAISES_PRIORITARIOS = [
    "Scotland",
    "Slovenia",
    "Slovakia",
    "Guatemala",
    "Romania",
    "Serbia",
    "Poland",
    "Sweden",
    "Tunisia",
    "Ukraine",
    "Brazil",
    "Argentina",
    "England",
    "France",
    "Germany",
    "Italy",
    "Portugal",
    "Spain",
    "USA",
    "Mexico",
]

TRADUCOES_PAISES = {
    "Scotland": "Escócia",
    "Slovenia": "Eslovênia",
    "Slovakia": "Eslováquia",
    "Guatemala": "Guatemala",
    "Romania": "Romênia",
    "Serbia": "Sérvia",
    "Poland": "Polônia",
    "Sweden": "Suécia",
    "Tunisia": "Tunísia",
    "Ukraine": "Ucrânia",
    "Brazil": "Brasil",
    "Argentina": "Argentina",
    "England": "Inglaterra",
    "France": "França",
    "Germany": "Alemanha",
    "Italy": "Itália",
    "Portugal": "Portugal",
    "Spain": "Espanha",
    "USA": "EUA",
    "Mexico": "México",
}

def traduzir_pais(nome: str) -> str:
    return TRADUCOES_PAISES.get(nome, nome)

@st.cache_data(ttl=900, show_spinner=False)
def buscar_fixtures_por_data(data_escolhida: str):
    url = f"{BASE_URL}/fixtures"
    params = {
        "date": data_escolhida,
        "timezone": "America/Maceio",
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def classificar_risco(status_curto: str) -> str:
    # só uma leitura simples
    if status_curto in ["NS", "TBD"]:
        return "Médio"
    if status_curto in ["1H", "HT", "2H", "LIVE"]:
        return "Ao vivo"
    if status_curto in ["FT", "AET", "PEN"]:
        return "Encerrado"
    return "Baixo"

def montar_linha(item: dict) -> dict:
    league = item.get("league", {})
    teams = item.get("teams", {})
    fixture = item.get("fixture", {})
    goals = item.get("goals", {})

    pais_api = league.get("country", "Outros")
    pais = traduzir_pais(pais_api)

    home = teams.get("home", {}).get("name", "Mandante")
    away = teams.get("away", {}).get("name", "Visitante")
    league_name = league.get("name", "Sem competição")
    horario = fixture.get("date", "")
    status_long = fixture.get("status", {}).get("long", "")
    status_short = fixture.get("status", {}).get("short", "")
    rodada = league.get("round", "")
    gols_casa = goals.get("home")
    gols_fora = goals.get("away")

    placar = "-"
    if gols_casa is not None and gols_fora is not None:
        placar = f"{gols_casa} x {gols_fora}"

    leitura = "Jogo do dia"
    if status_short in ["NS", "TBD"]:
        leitura = "Pré-jogo"
    elif status_short in ["1H", "HT", "2H", "LIVE"]:
        leitura = "Ao vivo"
    elif status_short in ["FT", "AET", "PEN"]:
        leitura = "Finalizado"

    return {
        "País": pais,
        "Competição": league_name,
        "Rodada": rodada,
        "Horário": pd.to_datetime(horario).strftime("%d/%m %H:%M") if horario else "",
        "Jogo": f"{home} x {away}",
        "Placar": placar,
        "Status": status_long,
        "Leitura": leitura,
        "Risco": classificar_risco(status_short),
        "FixtureID": fixture.get("id"),
    }

data_escolhida = st.date_input("Escolha a data dos jogos", value=date.today())

if st.button("Analisar agora"):
    try:
        resposta = buscar_fixtures_por_data(str(data_escolhida))

        if not resposta:
            st.warning("Nenhum jogo encontrado para essa data.")
            st.stop()

        linhas = [montar_linha(item) for item in resposta]
        df = pd.DataFrame(linhas)

        if df.empty:
            st.warning("Nenhum jogo válido encontrado.")
            st.stop()

        # prioriza os países que você quer
        df["prioritario"] = df["País"].apply(
            lambda x: 0 if x in [traduzir_pais(p) for p in PAISES_PRIORITARIOS] else 1
        )

        df = df.sort_values(
            ["prioritario", "País", "Competição", "Horário", "Jogo"]
        ).reset_index(drop=True)

        lista_paises = df["País"].dropna().unique().tolist()

        st.success(f"{len(df)} jogo(s) encontrado(s) em {len(lista_paises)} país(es).")

        c1, c2, c3 = st.columns(3)
        c1.metric("Jogos", len(df))
        c2.metric("Países", len(lista_paises))
        c3.metric("Competições", df["Competição"].nunique())

        tabs = st.tabs(lista_paises)

        for i, pais in enumerate(lista_paises):
            with tabs[i]:
                df_pais = df[df["País"] == pais].copy()

                competicoes = sorted(df_pais["Competição"].dropna().unique().tolist())
                selecionadas = st.multiselect(
                    f"Competições em {pais}",
                    competicoes,
                    default=competicoes,
                    key=f"comp_{pais}"
                )

                df_view = df_pais[df_pais["Competição"].isin(selecionadas)].copy()

                if df_view.empty:
                    st.info("Nenhum jogo restou após o filtro.")
                    continue

                st.dataframe(
                    df_view[["Competição", "Rodada", "Horário", "Jogo", "Placar", "Status", "Leitura", "Risco"]],
                    use_container_width=True,
                    hide_index=True,
                )

                csv = df_view.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    f"Baixar CSV - {pais}",
                    data=csv,
                    file_name=f"jogos_{pais}_{data_escolhida}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"csv_{pais}"
                )

    except requests.HTTPError as e:
        st.error(f"Erro HTTP da API: {e}")
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
