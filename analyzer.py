"""
Generador de análisis detallado para apuestas de valor.
"""


def generate_analysis(event: dict, selection: str, odd: float, prob: float) -> str:
    """
    Genera un análisis textual detallado de la apuesta con argumentos estadísticos.
    
    Args:
        event: Diccionario con información del evento
        selection: Nombre de la selección (equipo/jugador)
        odd: Cuota ofrecida
        prob: Probabilidad estimada
    
    Returns:
        Texto con el análisis detallado
    """
    sport = event.get("sport_key", "unknown")
    home = event.get("home_team", "")
    away = event.get("away_team", "")
    
    # Calcular métricas clave
    value = odd * prob
    value_pct = (value - 1) * 100
    implied_prob = (1 / odd) * 100
    edge = (prob * 100) - implied_prob
    
    # Determinar confianza
    if value_pct >= 15:
        confidence = " MUY ALTA"
    elif value_pct >= 10:
        confidence = " ALTA"
    elif value_pct >= 7:
        confidence = " MEDIA"
    else:
        confidence = "BAJA"
    
    # Generar argumentos específicos por deporte
    arguments = []
    
    if "basketball" in sport or "nba" in sport:
        arguments.append(" Análisis basado en forma reciente de equipos y eficiencia ofensiva/defensiva")
        arguments.append(f" La cuota {odd:.2f} subestima la probabilidad real del {selection}")
        if prob >= 0.60:
            arguments.append(f" Equipo favorito con {prob*100:.0f}% de probabilidad estimada")
        arguments.append(" Modelo considera: puntos por partido, victorias recientes, rendimiento local/visitante")
    
    elif "baseball" in sport or "mlb" in sport:
        arguments.append(" Análisis de forma actual y calidad de pitchers titulares")
        arguments.append(f" Cuota de {odd:.2f} vs probabilidad real de {prob*100:.1f}%")
        if prob >= 0.60:
            arguments.append(f" Equipo con {prob*100:.0f}% de probabilidad según estadísticas")
        arguments.append(" Factores: ERA de pitchers, rachas, rendimiento vs. rivales similares")
    
    elif "soccer" in sport or "football" in sport:
        arguments.append(" Modelo Poisson basado en goles esperados (xG)")
        arguments.append(f" Cuota {odd:.2f} ofrece {value_pct:+.1f}% de valor sobre la probabilidad real")
        if prob >= 0.55:
            arguments.append(f" Resultado con {prob*100:.0f}% de probabilidad según xG histórico")
        arguments.append(" Considera: ataque/defensa, goles a favor/contra, forma reciente")
    
    elif "tennis" in sport:
        arguments.append(" Análisis de ranking ATP/WTA y forma reciente")
        arguments.append(f" La cuota {odd:.2f} no refleja la ventaja real del jugador")
        if prob >= 0.60:
            arguments.append(f" Jugador con {prob*100:.0f}% de probabilidad según ranking y forma")
        arguments.append(" Factores: ranking, superficie, historial H2H, racha actual")
    
    # Argumentos generales de valor
    arguments.append(f" Edge del {edge:.1f}% sobre la probabilidad implícita del mercado")
    
    if value_pct >= 12:
        arguments.append(" OPORTUNIDAD EXCEPCIONAL: Valor significativamente alto")
    elif value_pct >= 9:
        arguments.append(" Buena oportunidad de valor según nuestro modelo")
    
    # ROI esperado
    expected_roi = (odd * prob - 1) * 100
    arguments.append(f" ROI esperado: {expected_roi:+.1f}% por unidad apostada")
    
    # Construir análisis completo
    analysis = f"""
 **ANÁLISIS DE VALOR DETALLADO**

**Partido:** {home} vs {away}
**Deporte:** {sport.upper()}
**Selección:** {selection}
**Cuota:** {odd:.2f}

 **MÉTRICAS CLAVE:**
 Probabilidad estimada: {prob*100:.1f}%
 Probabilidad implícita (cuota): {implied_prob:.1f}%
 Valor calculado: {value:.3f} ({value_pct:+.1f}%)
 Edge sobre el mercado: {edge:.1f}%
 ROI esperado: {expected_roi:+.1f}%
 Confianza: {confidence}

 **ARGUMENTOS Y RAZONES:**
"""
    
    for arg in arguments:
        analysis += f"\n{arg}"
    
    analysis += f"""

 **GESTIÓN:**
Gestiona tu bankroll con criterio Kelly o porcentaje fijo según tu tolerancia al riesgo.
Esta es una sugerencia informativa basada en modelos estadísticos.
"""
    
    return analysis.strip()
