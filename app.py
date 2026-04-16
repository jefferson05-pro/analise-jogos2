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

PAISES_PRIORITARIOS = [
    "Scotland", "Slovenia", "Slovakia", "Guatemala", "Romania",
    "Serbia", "Poland", "Sweden", "Tunisia", "Ukraine",
    "Brazil", "Argentina", "England", "France", "Germany",
    "Italy", "Portugal", "Spain", "USA", "Mexico"
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
    teams = item.get("teams", {})
    fixture = item.get("fixture", {})
    status_short = fixture.get("status", {}).get("short", "")

    score = 0
    league_name = (league.get("name") or "").lower()
    country_name = league.get("country") or ""

    if any(liga.lower() in league_name for liga in [x.lower() for x in LIGAS_DESTAQUE]):
        score += 35

    if country_name in PAISES_PRIORITARIOS:
        score += 15

    if teams.get("home", {}).get("winner") is None and teams.get("away", {}).get("winner") is None:
        score += 10

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
    rodada = league.get("round", "")
    status_long = fixture.get("status", {}).get("long", "")
    status_short = fixture.get("status", {}).get("short", "")
    horario_raw = fixture.get("date", "")

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

    horario = ""
    if horario_raw:
        horario = pd.to_datetime(horario_raw).strftime("%d/%m %H:%M")

    return {
        "País": pais,
        "Competição": league_name,
        "Rodada": rodada,
        "Horário": horario,
        "Jogo": f"{home} x {away}",
        "Placar": placar,
        "Status": status_long,
        "Leitura": leitura,
        "Risco": risco_por_status(status_short),
        "Nota": pontuar_jogo(item),
    }

def cor_risco(risco: str) -> str:
    if risco == "Baixo":
        return "#16a34a"
    if risco == "Médio":
        return "#d97706"
    if risco == "Ao vivo":
        return "#2563eb"
    if risco == "Encerrado":
        return "#6b7280"
    return "#6b7280"

def render_card(row, compact=False):
    risco = row["Risco"]
    cor = cor_risco(risco)

    meta1 = f"⏰ {row['Horário']}" if row["Horário"] else ""
    meta2 = f"🏆 {row['Competição']}"
    meta3 = f"📍 {row['País']}"

    extras = []
    if row["Rodada"]:
        extras.append(f"Rodada: {row['Rodada']}")
    if row["Placar"] and row["Placar"] != "-":
        extras.append(f"Placar: {row['Placar']}")
    extras.append(f"Status: {row['Status']}")
    extras.append(f"Nota: {row['Nota']}")

    extras_text = " • ".join(extras)

    size_title = "20px" if not compact else "18px"
    pad = "16px" if not compact else "14px"

    html = f"""
    <div style="
        background:#111827;
        border:1px solid #1f2937;
        border-radius:18px;
        padding:{pad};
        margin-bottom:12px;
        box-shadow:0 1px 6px rgba(0,0,0,0.20);
    ">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
            <div style="font-size:13px;color:#9ca3af;">{meta3}</div>
            <div style="
                background:{cor};
                color:white;
                padding:5px 10px;
                border-radius:999px;
                font-size:12px;
                font-weight:700;
            ">{risco}</div>
        </div>

        <div style="font-size:{size_title};font-weight:800;color:white;margin-top:10px;">
            {row["Jogo"]}
        </div>

        <div style="font-size:13px;color:#cbd5e1;margin-top:8px;line-height:1.6;">
            {meta1}<br>{meta2}
        </div>

        <div style="font-size:13px;color:#94a3b8;margin-top:10px;line-height:1.6;">
            {extras_text}
        </div>

        <div style="font-size:13px;color:#e5e7eb;margin-top:10px;font-weight:600;">
            {row["Leitura"]}
        </div>
    </div>
    """
    st.html(html)

st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
div[data-testid="stForm"] {
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 12px 12px 4px 12px;
    background: #0f172a;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise de Jogos")
st.caption("Ranking automático dos jogos do dia")

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
    top10 = df.head(10).copy()
    for _, row in top10.iterrows():
        render_card(row, compact=True)

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
        render_card(row)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar CSV do ranking",
        data=csv,
        file_name=f"ranking_jogos_{data_escolhida}.csv",
        mime="text/csv",
        use_container_width=True,
    )
