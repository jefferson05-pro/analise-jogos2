CODIGOS_PERMITIDOS = {
    "CL",   # Champions League
    "PL",   # Premier League
    "BL1",  # Bundesliga
    "PD",   # La Liga
    "SA",   # Serie A Itália
    "FL1",  # Ligue 1
    "DED",  # Eredivisie
    "PPL",  # Primeira Liga
    "BSA",  # Brasileirão Série A
    "WC",   # World Cup
    "EC"    # European Championship
}

competicoes = [c for c in listar_competicoes() if c.get("code") in CODIGOS_PERMITIDOS]
