import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

st.set_page_config(page_title="Análise de Jogos", layout="wide")

st.title("📊 Análise de Jogos")
st.caption("Análise automática das competições principais, com filtro por país")

API_TOKEN = st.secrets.get("FOOTBALL_DATA_API_TOKEN", None)

if not API_TOKEN:
    st.error("Token da API não encontrado. Vá em Settings > Secrets e adicione FOOTBALL_DATA_API_TOKEN.")
    st.stop()

HEADERS = {"X-Auth-Token": API_TOKEN}

LIGAS_PRIORITARIAS = [
    "Copa Libertadores",
    "Copa Sul-Americana",
    "Liga dos Campeões",
    "Champions League",
    "Copa do Nordeste",
    "Copa do Nordeste Superbet",
    "Parva Liga",
    "Primera División",
    "Prva Liga",
    "Liga Nacional",
    "Premier League",
    "Liga Profesional",
    "Bundesliga",
    "Liga Jupiler",
    "Brasileirão Betano",
    "Brasileirão Série A",
    "Brasileirão Série B",
    "Premier League do Canadá",
    "Liga de Primera",
    "Primeira A",
    "Liga Pro",
    "Liga Nike",
    "LaLiga2",
    "Copa do Rei",
    "MLS",
    "USL Championship",
    "Ligue 1",
    "Superliga",
    "NB I",
    "Championship",
    "Serie A",
    "Serie B",
    "Liga MX",
    "Liga de Expansão MX",
    "Liga Primera",
    "Eliteserien",
    "Copa de Primera",
    "Liga 1",
    "Liga Portugal",
    "Primeira Liga",
    "Chance Liga",
    "Super Lig",
    "Liga AUF Uruguaia",
    "Liga FUTVE",
    "Liga dos Campeões da CAF",
    "Premiership",
    "Campeonato da Fundação Motsepe",
    "Diski Challenge",
    "2. Bundesliga",
    "Série C",
    "Série D",
    "Alagoano 2",
    "Carioca 2",
    "Cearense 2",
    "Matogrossense 2",
    "Paranaense 2",
    "Paulista A3",
    "Paulista A4",
    "Liga de Ascenso",
    "Segunda División",
    "League One",
    "Copa da FA",
    "Liga do Chipre",
    "Divisão 2",
    "Primeira B",
    "Liga K1",
    "HNL",
    "Prva NL",
    "Druga NL",
    "1ª Divisão",
    "2ª Divisão",
    "Terceira Divisão",
    "Divisão 1",
    "Scottish Premiership",
    "Scottish Championship",
    "Scottish League One",
    "Scottish League Two",
    "Escócia Premiership",
    "Escócia Championship",
    "Eslovênia Prva Liga",
    "PrvaLiga",
    "Eslováquia Liga Nike",
    "Romênia Liga I",
    "Romênia SuperLiga",
    "SuperLiga",
    "Sérvia Super Liga",
    "Polônia Ekstraklasa",
    "Suécia Allsvenskan",
    "Suécia Superettan",
    "Tunísia Ligue Professionnelle 1",
    "Ucrânia Premier League",
    "Guatemala Liga Nacional",
]

MAPA_PAISES = {
    "Copa Libertadores": "América do Sul",
    "Copa Sul-Americana": "América do Sul",
    "Liga dos Campeões": "Europa",
    "Champions League": "Europa",
    "Copa do Nordeste": "Brasil",
    "Copa do Nordeste Superbet": "Brasil",
    "Parva Liga": "Bulgária",
    "Primera División": "El Salvador",
    "Prva Liga": "Eslovênia",
    "Liga Nacional": "Honduras",
    "Premier League": "Inglaterra",
    "Liga Profesional": "Argentina",
    "Bundesliga": "Alemanha",
    "Liga Jupiler": "Bélgica",
    "Brasileirão Betano": "Brasil",
    "Brasileirão Série A": "Brasil",
    "Brasileirão Série B": "Brasil",
    "Premier League do Canadá": "Canadá",
    "Liga de Primera": "Chile",
    "Primeira A": "Colômbia",
    "Liga Pro": "Equador",
    "Liga Nike": "Eslováquia",
    "LaLiga2": "Espanha",
    "Copa do Rei": "Espanha",
    "MLS": "EUA",
    "USL Championship": "EUA",
    "Ligue 1": "França",
    "Superliga": "Grécia",
    "NB I": "Hungria",
    "Championship": "Inglaterra",
    "Serie A": "Itália",
    "Serie B": "Itália",
    "Liga MX": "México",
    "Liga de Expansão MX": "México",
    "Liga Primera": "Nicarágua",
    "Eliteserien": "Noruega",
    "Copa de Primera": "Paraguai",
    "Liga 1": "Peru",
    "Liga Portugal": "Portugal",
    "Primeira Liga": "Portugal",
    "Chance Liga": "República Tcheca",
    "Super Lig": "Turquia",
    "Liga AUF Uruguaia": "Uruguai",
    "Liga FUTVE": "Venezuela",
    "Liga dos Campeões da CAF": "África",
    "Premiership": "África do Sul",
    "Campeonato da Fundação Motsepe": "África do Sul",
    "Diski Challenge": "África do Sul",
    "2. Bundesliga": "Alemanha",
    "Série C": "Brasil",
    "Série D": "Brasil",
    "Alagoano 2": "Brasil",
    "Carioca 2": "Brasil",
    "Cearense 2": "Brasil",
    "Matogrossense 2": "Brasil",
    "Paranaense 2": "Brasil",
    "Paulista A3": "Brasil",
    "Paulista A4": "Brasil",
    "Liga de Ascenso": "Costa Rica",
    "Segunda División": "Chile",
    "League One": "China",
    "Copa da FA": "China",
    "Liga do Chipre": "Chipre",
    "Divisão 2": "Chipre",
    "Primeira B": "Colômbia",
    "Liga K1": "Coreia do Sul",
    "HNL": "Croácia",
    "Prva NL": "Croácia",
    "Druga NL": "Croácia",
    "1ª Divisão": "Dinamarca",
    "2ª Divisão": "Dinamarca",
    "Terceira Divisão": "Dinamarca",
    "Divisão 1": "Emirados Árabes",
    "Scottish Premiership": "Escócia",
    "Scottish Championship": "Escócia",
    "Scottish League One": "Escócia",
    "Scottish League Two": "Escócia",
    "Escócia Premiership": "Escócia",
    "Escócia Championship": "Escócia",
    "Eslovênia Prva Liga": "Eslovênia",
    "PrvaLiga": "Eslovênia",
    "Eslováquia Liga Nike": "Eslováquia",
    "Romênia Liga I": "Romênia",
    "Romênia SuperLiga": "Romênia",
    "SuperLiga": "Sérvia",
    "Sérvia Super Liga": "Sérvia",
    "Polônia Ekstraklasa": "Polônia",
    "Suécia Allsvenskan": "Suécia",
    "Suécia Superettan": "Suécia",
    "Tunísia Ligue Professionnelle 1": "Tunísia",
    "Ucrânia Premier League": "Ucrânia",
    "Guatemala Liga Nacional": "Guatemala",
}


def listar_competicoes():
    url = "https://api.football-data.org/v4/competitions"
    resposta = requests.get(url, timeout=30)
    resposta.raise_for_status()
    return resposta.json().get("competitions", [])


def buscar_jogos_competicao(codigo_competicao, data_escolhida):
    url = f"https://api.football-data.org/v4/competitions/{codigo_competicao}/matches"
    params = {
        "dateFrom": data_escolhida.isoformat(),
        "dateTo": data_escolhida.isoformat(),
    }
    resposta = requests.get(url, headers=HEADERS, params=params, timeout=30)

    if resposta.status_code in (400, 403, 404):
        return []

    resposta.raise_for_status()
    return resposta.json().get("matches", [])


def pontos_resultado(time_id, partida):
    score = partida.get("score", {})
    winner = score.get("winner")
    home_id = partida.get("homeTeam", {}).get("id")
    away_id = partida.get("awayTeam", {}).get("id")

    if winner == "DRAW":
        return 1
    if winner == "HOME_TEAM" and time_id == home_id:
        return 3
    if winner == "AWAY_TEAM" and time_id == away_id:
        return 3
    return 0


def gols_time(time_id, partida):
    full = partida.get("score", {}).get("fullTime", {})
    home_id = partida.get("homeTeam", {}).get("id")
    away_id = partida.get("awayTeam", {}).get("id")
    home_goals = full.get("home")
    away_goals = full.get("away")

    if home_goals is None or away_goals is None:
        return 0, 0

    if time_id == home_id:
        return home_goals, away_goals
    if time_id == away_id:
        return away_goals, home_goals
    return 0, 0


def buscar_forma_time(team_id, data_escolhida):
    data_inicio = (data_escolhida - timedelta(days=120)).isoformat()
    data_fim = (data_escolhida - timedelta(days=1)).isoformat()

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
    params = {
        "dateFrom": data_inicio,
        "dateTo": data_fim,
        "status": "FINISHED",
        "limit": 10,
    }

    resposta = requests.get(url, headers=HEADERS, params=params, timeout=30)

    if resposta.status_code in (400, 403, 404):
        return {"pts": 1.0, "gf": 1.0, "ga": 1.0}

    resposta.raise_for_status()
    partidas = resposta.json().get("matches", [])[-5:]

    if not partidas:
        return {"pts": 1.0, "gf": 1.0, "ga": 1.0}

    pontos = []
    gols_feitos = []
    gols_sofridos = []

    for partida in partidas:
        pontos.append(pontos_resultado(team_id, partida))
        gf, ga = gols_time(team_id, partida)
        gols_feitos.append(gf)
        gols_sofridos.append(ga)

    return {
        "pts": round(sum(pontos) / len(pontos), 2),
        "gf": round(sum(gols_feitos) / len(gols_feitos), 2),
        "ga": round(sum(gols_sofridos) / len(gols_sofridos), 2),
    }


def classificar_jogo(casa, fora):
    forca_casa = (casa["pts"] * 1.8) + (casa["gf"] * 0.7) - (casa["ga"] * 0.5)
    forca_fora = (fora["pts"] * 1.8) + (fora["gf"] * 0.7) - (fora["ga"] * 0.5)

    delta = round(forca_casa - forca_fora, 2)
    indice_gols = round(casa["gf"] + fora["gf"] + 0.5 * (casa["ga"] + fora["ga"]), 2)

    if delta >= 1.5:
        tendencia = "Mandante mais forte"
        confianca = 74
    elif delta >= 0.6:
        tendencia = "Leve vantagem do mandante"
        confianca = 63
    elif delta <= -1.5:
        tendencia = "Visitante mais forte"
        confianca = 74
    elif delta <= -0.6:
        tendencia = "Leve vantagem do visitante"
        confianca = 63
    else:
        tendencia = "Jogo equilibrado"
        confianca = 54

    if indice_gols >= 3.6:
        gols = "Tendência de gols"
    elif indice_gols >= 2.5:
        gols = "Tendência moderada de gols"
    else:
        gols = "Tendência de poucos gols"

    if abs(delta) < 0.6:
        risco = "Alto"
    elif abs(delta) < 1.2:
        risco = "Médio"
    else:
        risco = "Baixo"

    return tendencia, gols, risco, confianca


def eh_liga_prioritaria(nome_competicao):
    nome = (nome_competicao or "").strip().lower()
    lista = [liga.lower() for liga in LIGAS_PRIORITARIAS]
    return any(liga in nome or nome in liga for liga in lista)


def descobrir_pais(nome_competicao):
    nome = (nome_competicao or "").strip().lower()

    for liga, pais in MAPA_PAISES.items():
        liga_lower = liga.lower()
        if liga_lower in nome or nome in liga_lower:
            return pais

    return "Outros"


data_escolhida = st.date_input("Escolha a data dos jogos", value=date.today())

if st.button("Analisar agora"):
    try:
        competicoes = listar_competicoes()

        if not competicoes:
            st.warning("Nenhuma competição encontrada.")
            st.stop()

        todas_partidas = []

        with st.spinner("Buscando competições e jogos da data..."):
            for comp in competicoes:
                codigo = comp.get("code")
                nome = comp.get("name", "Sem competição")

                if not codigo:
                    continue

                partidas = buscar_jogos_competicao(codigo, data_escolhida)

                for partida in partidas:
                    if not partida.get("competition"):
                        partida["competition"] = {}
                    if not partida["competition"].get("name"):
                        partida["competition"]["name"] = nome
                    todas_partidas.append(partida)

        if not todas_partidas:
            st.warning("Nenhum jogo encontrado nas competições acessíveis para essa data.")
            st.stop()

        linhas = []

        for partida in todas_partidas:
            home = partida.get("homeTeam", {})
            away = partida.get("awayTeam", {})

            home_id = home.get("id")
            away_id = away.get("id")

            if not home_id or not away_id:
                continue

            nome_competicao = partida.get("competition", {}).get("name", "Sem competição")

            if not eh_liga_prioritaria(nome_competicao):
                continue

            forma_casa = buscar_forma_time(home_id, data_escolhida)
            forma_fora = buscar_forma_time(away_id, data_escolhida)

            tendencia, gols, risco, confianca = classificar_jogo(forma_casa, forma_fora)

            horario = pd.to_datetime(
                partida.get("utcDate"), utc=True
            ).tz_convert("America/Maceio").strftime("%d/%m %H:%M")

            linhas.append({
                "País": descobrir_pais(nome_competicao),
                "Competição": nome_competicao,
                "Horário": horario,
                "Jogo": f"{home.get('name', 'Mandante')} x {away.get('name', 'Visitante')}",
                "Tendência": tendencia,
                "Gols": gols,
                "Risco": risco,
                "Confiança": confianca,
            })

        df = pd.DataFrame(linhas)

        if df.empty:
            st.warning("Nenhum jogo encontrado dentro da sua lista principal de ligas.")
            st.stop()

        df = df.sort_values(["País", "Competição", "Horário", "Jogo"]).reset_index(drop=True)

        lista_paises = sorted(df["País"].dropna().unique().tolist())
        paises_selecionados = st.multiselect(
            "Filtrar por país",
            lista_paises,
            default=lista_paises
        )

        df = df[df["País"].isin(paises_selecionados)].copy()

        if df.empty:
            st.warning("Nenhum jogo restou após o filtro por país.")
            st.stop()

        lista_competicoes = sorted(df["Competição"].dropna().unique().tolist())
        selecionadas = st.multiselect(
            "Competições encontradas na data (A-Z)",
            lista_competicoes,
            default=lista_competicoes
        )

        df_filtrado = df[df["Competição"].isin(selecionadas)].copy()

        if df_filtrado.empty:
            st.warning("Nenhum jogo restou após o filtro.")
            st.stop()

        st.success(f"{len(df_filtrado)} jogo(s) analisado(s) em {len(selecionadas)} competição(ões).")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jogos", len(df_filtrado))
        c2.metric("Países", len(paises_selecionados))
        c3.metric("Risco baixo", int((df_filtrado["Risco"] == "Baixo").sum()))
        c4.metric("Confiança média", f"{round(df_filtrado['Confiança'].mean(), 1)}%")

        mostrar = df_filtrado.copy()
        mostrar["Confiança"] = mostrar["Confiança"].astype(int).astype(str) + "%"

        st.dataframe(mostrar, use_container_width=True, hide_index=True)

        csv = mostrar.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Baixar CSV",
            data=csv,
            file_name=f"analise_jogos_{data_escolhida}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
