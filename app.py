import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

st.set_page_config(page_title="Análise de Jogos", layout="wide")

st.title("📊 Análise de Jogos")
st.caption("Análise automática das competições principais, com abas por país")

API_TOKEN = st.secrets.get("FOOTBALL_DATA_API_TOKEN", None)

if not API_TOKEN:
    st.error("Token da API não encontrado. Vá em Settings > Secrets e adicione FOOTBALL_DATA_API_TOKEN.")
    st.stop()

HEADERS = {"X-Auth-Token": API_TOKEN}

# Lista fixa de competições/códigos
# Alguns códigos podem não estar disponíveis no seu plano/token.
COMPETICOES_FIXAS = [
    {"code": "CL", "name": "Champions League", "country": "Europa"},
    {"code": "BSA", "name": "Brasileirão Série A", "country": "Brasil"},
    {"code": "PL", "name": "Premier League", "country": "Inglaterra"},
    {"code": "ELC", "name": "Championship", "country": "Inglaterra"},
    {"code": "BL1", "name": "Bundesliga", "country": "Alemanha"},
    {"code": "SA", "name": "Serie A", "country": "Itália"},
    {"code": "FL1", "name": "Ligue 1", "country": "França"},
    {"code": "DED", "name": "Eredivisie", "country": "Holanda"},
    {"code": "PPL", "name": "Primeira Liga", "country": "Portugal"},
    {"code": "PD", "name": "La Liga", "country": "Espanha"},
]

def buscar_jogos_competicao(codigo_competicao, data_escolhida):
    url = f"https://api.football-data.org/v4/competitions/{codigo_competicao}/matches"
    params = {
        "dateFrom": data_escolhida.isoformat(),
        "dateTo": data_escolhida.isoformat(),
    }
    resposta = requests.get(url, headers=HEADERS, params=params, timeout=30)

    if resposta.status_code in (400, 401, 403, 404):
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

    if resposta.status_code in (400, 401, 403, 404):
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

data_escolhida = st.date_input("Escolha a data dos jogos", value=date.today())

if st.button("Analisar agora"):
    try:
        todas_partidas = []

        with st.spinner("Buscando jogos das competições configuradas..."):
            for comp in COMPETICOES_FIXAS:
                partidas = buscar_jogos_competicao(comp["code"], data_escolhida)

                for partida in partidas:
                    if not partida.get("competition"):
                        partida["competition"] = {}
                    partida["competition"]["name"] = comp["name"]
                    partida["competition"]["area_name"] = comp["country"]
                    todas_partidas.append(partida)

        if not todas_partidas:
            st.warning("Nenhum jogo encontrado nas competições configuradas para essa data.")
            st.stop()

        linhas = []

        for partida in todas_partidas:
            home = partida.get("homeTeam", {})
            away = partida.get("awayTeam", {})

            home_id = home.get("id")
            away_id = away.get("id")

            if not home_id or not away_id:
                continue

            forma_casa = buscar_forma_time(home_id, data_escolhida)
            forma_fora = buscar_forma_time(away_id, data_escolhida)

            tendencia, gols, risco, confianca = classificar_jogo(forma_casa, forma_fora)

            horario = pd.to_datetime(
                partida.get("utcDate"), utc=True
            ).tz_convert("America/Maceio").strftime("%d/%m %H:%M")

            linhas.append({
                "País": partida.get("competition", {}).get("area_name", "Outros"),
                "Competição": partida.get("competition", {}).get("name", "Sem competição"),
                "Horário": horario,
                "Jogo": f"{home.get('name', 'Mandante')} x {away.get('name', 'Visitante')}",
                "Tendência": tendencia,
                "Gols": gols,
                "Risco": risco,
                "Confiança": confianca,
            })

        df = pd.DataFrame(linhas)

        if df.empty:
            st.warning("Nenhum jogo válido encontrado.")
            st.stop()

        df = df.sort_values(["País", "Competição", "Horário", "Jogo"]).reset_index(drop=True)

        paises = sorted(df["País"].dropna().unique().tolist())

        st.success(f"{len(df)} jogo(s) analisado(s) em {len(paises)} país(es).")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jogos", len(df))
        c2.metric("Países", len(paises))
        c3.metric("Risco baixo", int((df["Risco"] == "Baixo").sum()))
        c4.metric("Confiança média", f"{round(df['Confiança'].mean(), 1)}%")

        abas = st.tabs(paises)

        for i, pais in enumerate(paises):
            with abas[i]:
                df_pais = df[df["País"] == pais].copy()

                mostrar = df_pais.copy()
                mostrar["Confiança"] = mostrar["Confiança"].astype(int).astype(str) + "%"

                st.dataframe(mostrar, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
