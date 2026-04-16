import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="Análise de Jogos", layout="wide")

API_KEY = st.secrets.get("API_FOOTBALL_KEY")

if not API_KEY:
    st.error("Chave não encontrada. Vá em Settings > Secrets e adicione API_FOOTBALL_KEY.")
    st.stop()

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

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

LIGAS_DESTAQUE = [
    "UEFA Champions League",
    "CONMEBOL Libertadores",
    "CONMEBOL Sudamericana",
    "Serie A",
    "Premier League",
    "Bundesliga",
    "Ligue 1",
    "La Liga",
    "Primeira Liga",
    "Brasileirão",
    "MLS",
    "Liga MX",
    "Championship",
    "Ekstraklasa",
    "Allsvenskan",
    "Superettan",
    "Liga I",
    "Super Liga",
    "Niké Liga",
    "PrvaLiga",
]

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

@st.cache_data(ttl=900, show_spinner=False)
def buscar_classificacao(league_id: int, season: int):
    url = f"{BASE_URL}/standings"
    params = {
        "league": league_id,
        "season": season,
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code in (400, 401, 403, 404):
        return {}
    r.raise_for_status()
    data = r.json().get("response", [])
    if not data:
        return {}

    # A API pode retornar grupos; juntamos todos os times
    tabela = {}
    league_block = data[0].get("league", {})
    standings_groups = league_block.get("standings", [])

    for group in standings_groups:
        for row in group:
            team = row.get("team", {})
            team_id = team.get("id")
            all_stats = row.get("all", {})
            tabela[team_id] = {
                "rank": row.get("rank"),
                "points": row.get("points", 0),
                "played": all_stats.get("played", 0),
                "win": all_stats.get("win", 0),
                "draw": all_stats.get("draw", 0),
                "lose": all_stats.get("lose", 0),
                "goals_for": all_stats.get("goals", {}).get("for", 0),
                "goals_against": all_stats.get("goals", {}).get("against", 0),
                "goal_diff": row.get("goalsDiff", 0),
                "form": row.get("form", ""),
            }
    return tabela

def risco_por_status(status_curto: str) -> str:
    if status_curto in ["NS", "TBD"]:
        return "Médio"
    if status_curto in ["1H", "HT", "2H", "LIVE"]:
        return "Ao vivo"
    if status_curto in ["FT", "AET", "PEN"]:
        return "Encerrado"
    return "Baixo"

def pontuar_jogo(item: dict) -> int:
    league = item.get("league", {})
    fixture = item.get("fixture", {})
    status_short = fixture.get("status", {}).get("short", "")

    score = 0
    league_name = (league.get("name") or "").lower()

    if any(liga.lower() in league_name for liga in [x.lower() for x in LIGAS_DESTAQUE]):
        score += 35

    if status_short in ["NS", "TBD"]:
        score += 20
    elif status_short in ["1H", "HT", "2H", "LIVE"]:
        score += 12
    else:
        score += 3

    round_name = (league.get("round") or "").lower()
    if any(x in round_name for x in ["quarter", "semi", "final", "playoff"]):
        score += 8

    return score

def score_form_string(form: str) -> float:
    # W=3, D=1, L=0
    pts = 0
    for ch in (form or "").upper():
        if ch == "W":
            pts += 3
        elif ch == "D":
            pts += 1
    return pts

def estimar_leitura_por_tabela(item: dict):
    league = item.get("league", {})
    teams = item.get("teams", {})

    league_name = league.get("name", "")
    league_id = league.get("id")
    season = league.get("season")

    home = teams.get("home", {})
    away = teams.get("away", {})
    home_id = home.get("id")
    away_id = away.get("id")
    home_name = home.get("name", "Mandante")
    away_name = away.get("name", "Visitante")

    tabela = buscar_classificacao(league_id, season) if league_id and season else {}

    # fallback neutro quando não houver tabela
    if not tabela or home_id not in tabela or away_id not in tabela:
        return "Empate bem possível", "Média", 55, "Sem dados completos de tabela; cenário equilibrado."

    h = tabela[home_id]
    a = tabela[away_id]

    # score de força simples
    # mais pontos, melhor rank, saldo, forma recente
    score_home = 0.0
    score_away = 0.0

    score_home += h["points"] * 1.0
    score_away += a["points"] * 1.0

    score_home += h["goal_diff"] * 0.35
    score_away += a["goal_diff"] * 0.35

    score_home += score_form_string(h["form"]) * 0.8
    score_away += score_form_string(a["form"]) * 0.8

    # rank menor é melhor
    if h["rank"] and a["rank"]:
        score_home += max(0, 25 - h["rank"]) * 0.8
        score_away += max(0, 25 - a["rank"]) * 0.8

    # mando leve, mas não dominante
    score_home += 2.0

    delta = round(score_home - score_away, 2)

    # favoritismo de 3 vias
    if delta >= 8:
        favoritismo = "Mandante mais forte"
        confianca = 73
    elif delta >= 3:
        favoritismo = "Mandante com leve vantagem"
        confianca = 64
    elif delta <= -8:
        favoritismo = "Visitante mais forte"
        confianca = 73
    elif delta <= -3:
        favoritismo = "Visitante com leve vantagem"
        confianca = 64
    else:
        favoritismo = "Empate bem possível"
        confianca = 58

    # tendência de gols
    gols_por_jogo_home = (h["goals_for"] + h["goals_against"]) / h["played"] if h["played"] else 0
    gols_por_jogo_away = (a["goals_for"] + a["goals_against"]) / a["played"] if a["played"] else 0
    media_total = (gols_por_jogo_home + gols_por_jogo_away) / 2

    if media_total >= 3.0:
        tendencia_gols = "Alta"
    elif media_total >= 2.2:
        tendencia_gols = "Média"
    else:
        tendencia_gols = "Baixa"

    # resumo curto
    if favoritismo == "Empate bem possível":
        resumo = "Diferença pequena entre os times na tabela."
    elif "Mandante" in favoritismo:
        resumo = f"{home_name} aparece melhor na classificação e no momento recente."
    else:
        resumo = f"{away_name} aparece melhor na classificação e no momento recente."

    return favoritismo, tendencia_gols, confianca, resumo

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
    horario_raw = fixture.get("date", "")
    status_long = fixture.get("status", {}).get("long", "")
    status_short = fixture.get("status", {}).get("short", "")

    horario = ""
    if horario_raw:
        horario = pd.to_datetime(horario_raw).strftime("%d/%m %H:%M")

    gols_casa = goals.get("home")
    gols_fora = goals.get("away")
    placar = "-"
    if gols_casa is not None and gols_fora is not None:
        placar = f"{gols_casa} x {gols_fora}"

    favoritismo, tendencia_gols, confianca, resumo = estimar_leitura_por_tabela(item)

    return {
        "País": pais,
        "Competição": league_name,
        "Horário": horario,
        "Jogo": f"{home} x {away}",
        "Placar": placar,
        "Status": status_long,
        "Risco": risco_por_status(status_short),
        "Nota": pontuar_jogo(item),
        "Favoritismo": favoritismo,
        "Tendência de gols": tendencia_gols,
        "Confiança": confianca,
        "Resumo": resumo,
    }

def linha_resumo(row):
    return f"{row['Favoritismo']} | Gols {row['Tendência de gols']} | Confiança {row['Confiança']}"

def render_card_3_linhas(row):
    with st.container(border=True):
        st.markdown(f"**{row['Jogo']}**")
        st.caption(f"{row['País']} • {row['Competição']} • {row['Horário']}")
        st.write(linha_resumo(row))

st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 850px;
}
div[data-testid="stForm"] {
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 12px 12px 4px 12px;
}
div[data-testid="stMetric"] {
    border: 1px solid #1f2937;
    padding: 10px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise de Jogos")
st.caption("Leitura neutra dos jogos do dia com 3 saídas: mandante, empate ou visitante")

data_escolhida = st.date_input("Escolha a data dos jogos", value=date.today())

if st.button("Analisar agora", use_container_width=True):
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

        df = df.sort_values(
            ["Nota", "País", "Competição", "Horário"],
            ascending=[False, True, True, True]
        ).reset_index(drop=True)

        st.session_state["df_jogos"] = df
        st.session_state["paises"] = sorted(df["País"].dropna().unique().tolist())

        if "pais_filtro" not in st.session_state:
            st.session_state["pais_filtro"] = st.session_state["paises"]

        if "comp_filtro" not in st.session_state:
            st.session_state["comp_filtro"] = sorted(df["Competição"].dropna().unique().tolist())

    except requests.HTTPError as e:
        st.error(f"Erro HTTP da API: {e}")
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")

if "df_jogos" in st.session_state:
    df = st.session_state["df_jogos"].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jogos", len(df))
    c2.metric("Competições", df["Competição"].nunique())
    c3.metric("Países", df["País"].nunique())
    c4.metric("Top nota", int(df["Nota"].max()))

    st.subheader("🏆 Top 10 jogos do dia")
    for _, row in df.head(10).iterrows():
        render_card_3_linhas(row)

    st.subheader("🔎 Filtros")
    with st.form("form_filtros"):
        lista_paises = sorted(df["País"].dropna().unique().tolist())
        paises_selecionados = st.multiselect(
            "Países",
            lista_paises,
            default=st.session_state.get("pais_filtro", lista_paises),
        )

        df_temp = df[df["País"].isin(paises_selecionados)].copy()
        lista_competicoes = sorted(df_temp["Competição"].dropna().unique().tolist())

        default_comp = [
            c for c in st.session_state.get("comp_filtro", lista_competicoes)
            if c in lista_competicoes
        ]
        if not default_comp:
            default_comp = lista_competicoes

        competicoes_selecionadas = st.multiselect(
            "Competições",
            lista_competicoes,
            default=default_comp,
        )

        aplicar = st.form_submit_button("Aplicar filtros", use_container_width=True)

    if aplicar:
        st.session_state["pais_filtro"] = paises_selecionados
        st.session_state["comp_filtro"] = competicoes_selecionadas

    paises_aplicados = st.session_state.get("pais_filtro", lista_paises)
    df = df[df["País"].isin(paises_aplicados)].copy()

    comps_disponiveis = sorted(df["Competição"].dropna().unique().tolist())
    comps_aplicadas = [
        c for c in st.session_state.get("comp_filtro", comps_disponiveis)
        if c in comps_disponiveis
    ]

    if not comps_aplicadas:
        st.warning("Nenhuma competição selecionada.")
        st.stop()

    df = df[df["Competição"].isin(comps_aplicadas)].copy()

    if df.empty:
        st.warning("Nenhum jogo restou após os filtros.")
        st.stop()

    st.subheader("📋 Lista completa")
    for _, row in df.iterrows():
        render_card_3_linhas(row)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar CSV do ranking",
        data=csv,
        file_name=f"ranking_jogos_{data_escolhida}.csv",
        mime="text/csv",
        use_container_width=True,
    )
