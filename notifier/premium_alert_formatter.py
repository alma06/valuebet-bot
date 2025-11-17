"""
notifier/premium_alert_formatter.py - Formateador optimizado para alertas premium exclusivas

Genera mensajes premium con:
- Probabilidades ajustadas en tiempo real
- Información de calidad y confianza
- Datos de alineaciones y lesiones
- Valor recalculado con información actual
"""

from typing import Dict
from datetime import datetime
import sys
from pathlib import Path

# Asegurar que utils esté en el path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sport_translator import translate_sport


def format_premium_exclusive_alert(candidate: Dict, user, stake: float) -> str:
    """
    Mensaje premium exclusivo con información ajustada en tiempo real
    """
    lines = []
    
    # Header premium exclusivo
    lines.append("🏆━━━━━━━━━━━━━━━━━━━━━━🏆")
    lines.append("💎 ALERTA PREMIUM EXCLUSIVA 💎")
    
    # Mostrar ranking de calidad
    quality_rank = candidate.get('quality_rank', 1)
    total_candidates = candidate.get('total_candidates', 1)
    quality_score = candidate.get('quality_score', 0.8)
    
    lines.append(f"🎯 **TOP #{quality_rank}** de {total_candidates} candidatos")
    lines.append(f"⭐ **Calidad:** {quality_score:.1%} de confianza")
    lines.append("🏆━━━━━━━━━━━━━━━━━━━━━━🏆")
    lines.append("")
    
    # Información del evento
    sport_es = translate_sport(candidate.get('sport_key', ''), candidate.get('sport'))
    lines.append(f"🎯 **{sport_es.upper()}**")
    lines.append(f"⚽ **{candidate.get('event', 'N/A')}**")
    lines.append("")
    
    # Mercado y selección
    market_name = _get_market_name_spanish(candidate.get('market_key', ''))
    lines.append(f"📊 **MERCADO:** {market_name}")
    lines.append(f"✅ **PRONÓSTICO:** {candidate['selection']}")
    
    # Información adicional del mercado 
    if candidate.get('point') is not None:
        lines.append(f"📏 **Línea:** {candidate['point']:+.1f}")
    if candidate.get('total') is not None:
        lines.append(f"📈 **Total:** {candidate['total']}")
    
    lines.append("")
    
    # Información de cuotas y casa
    odds = candidate.get('odds', 2.0)
    lines.append(f"💰 **CUOTA:** {odds:.2f}")
    lines.append(f"🏠 **CASA:** {candidate.get('bookmaker', 'N/A')}")
    
    # Link si está disponible
    if candidate.get('url'):
        lines.append(f"🔗 **Link:** {candidate['url']}")
    
    lines.append("")
    
    # ANÁLISIS CON INFORMACIÓN AJUSTADA
    lines.append("📈 **ANÁLISIS PREMIUM ACTUALIZADO:**")
    
    # Probabilidades ajustadas vs originales
    original_prob = candidate.get('original_probability', 0.55) * 100
    adjusted_prob = candidate.get('prob_calculated', candidate.get('real_probability', 55))
    if adjusted_prob <= 1:  # Si está en decimal
        adjusted_prob *= 100
    
    prob_adjustment = candidate.get('probability_adjustment', 0.0) * 100
    
    lines.append(f"🔢 **Prob. Original:** {original_prob:.1f}%")
    lines.append(f"🔄 **Prob. Ajustada:** {adjusted_prob:.1f}%")
    if abs(prob_adjustment) > 0.5:  # Solo mostrar si es significativo
        direction = "⬆️" if prob_adjustment > 0 else "⬇️"
        lines.append(f"{direction} **Ajuste:** {prob_adjustment:+.1f}% (info tiempo real)")
    
    # Valor original vs ajustado
    original_value = candidate.get('original_value', odds * (original_prob/100))
    current_value = candidate.get('value', odds * (adjusted_prob/100))
    
    lines.append(f"💎 **Valor Original:** {original_value:.3f}")
    lines.append(f"✨ **Valor Ajustado:** {current_value:.3f}")
    
    if current_value > original_value:
        lines.append("📈 **Mejora con información actual** ✅")
    elif current_value < original_value:
        lines.append("📉 **Valor reducido por nueva información** ⚠️")
    
    lines.append("")
    
    # Información de confianza
    confidence_score = candidate.get('confidence_score', 0.8)
    lines.append(f"🎯 **NIVEL DE CONFIANZA:** {confidence_score:.1%}")
    
    # Breakdown de calidad si está disponible
    quality_breakdown = candidate.get('quality_breakdown', {})
    if quality_breakdown:
        scores = quality_breakdown.get('scores', {})
        if scores:
            lines.append("📊 **Factores de Calidad:**")
            
            # Mostrar factores más importantes
            if scores.get('confidence_score', 0) > 0.7:
                lines.append(f"  ✅ Información confiable ({scores['confidence_score']:.1%})")
            if scores.get('value', 0) > 0.7:
                lines.append(f"  💰 Excelente valor ({scores['value']:.1%})")
            if scores.get('probability_adjustment', 0) > 0.5:
                lines.append(f"  🔄 Ajuste significativo con datos reales")
            if scores.get('data_quality', 0) > 0.8:
                lines.append(f"  📊 Datos deportivos de alta calidad")
    
    lines.append("")
    
    # Información de ajustes aplicados
    adjustment_details = candidate.get('adjustment_details', {})
    if adjustment_details and adjustment_details.get('reasoning'):
        lines.append("🔍 **AJUSTES APLICADOS:**")
        reasoning = adjustment_details['reasoning']
        lines.append(f"📝 {reasoning}")
        lines.append("")
    
    # Información deportiva resumida
    sports_info = candidate.get('sports_info_summary', {})
    if sports_info:
        data_quality = sports_info.get('data_quality', 'MEDIUM')
        last_updated = sports_info.get('last_updated', 'N/A')
        
        lines.append("🏥 **INFORMACIÓN DEPORTIVA:**")
        lines.append(f"📊 **Calidad de datos:** {data_quality}")
        
        if last_updated != 'N/A':
            try:
                update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                time_str = update_time.strftime('%H:%M UTC')
                lines.append(f"🕐 **Última actualización:** {time_str}")
            except:
                pass
        
        lines.append("⚠️ **Verificar alineaciones 1-2h antes del juego**")
        lines.append("")
    
    # Gestión de bankroll premium
    lines.append("💰 **GESTIÓN DE BANKROLL:**")
    bankroll = user.get('bankroll', getattr(user, 'bankroll', 1000))
    lines.append(f"💵 **Bankroll actual:** ${bankroll:.2f}")
    lines.append(f"🎯 **Stake recomendado:** ${stake:.2f}")
    lines.append(f"📊 **Porcentaje:** {(stake/bankroll)*100:.1f}%")
    lines.append("")
    
    # Recomendación final
    if current_value >= 1.08:
        recommendation = "🚀 **APUESTA FUERTE** - Valor excepcional confirmado"
        confidence_emoji = "🔥"
    elif current_value >= 1.05:
        recommendation = "✅ **APUESTA RECOMENDADA** - Buen valor ajustado"
        confidence_emoji = "✅"
    elif current_value >= 1.02:
        recommendation = "⚠️ **APUESTA CAUTELOSA** - Valor marginal"
        confidence_emoji = "⚠️"
    else:
        recommendation = "❌ **NO APOSTAR** - Valor insuficiente tras ajustes"
        confidence_emoji = "❌"
    
    lines.append(f"{confidence_emoji} **RECOMENDACIÓN FINAL:**")
    lines.append(recommendation)
    lines.append("")
    
    # Consejos premium
    lines.append("💡 **CONSEJOS PREMIUM:**")
    lines.append("🔍 **1.** Verifica alineaciones antes de apostar")
    lines.append("📈 **2.** Busca mejores cuotas en otras casas (+0.02-0.05)")
    lines.append("💰 **3.** Considera bankroll total antes de apostar")
    lines.append("📊 **4.** Registra resultado para tracking personal")
    lines.append("")
    
    # Footer premium
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🏆 **PREMIUM EXCLUSIVE** 🏆")
    lines.append("📊 Análisis actualizado en tiempo real")
    lines.append("🎯 Solo las 5 mejores oportunidades diarias")
    lines.append("💎 Información de calidad institucional")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_free_user_upgrade_message() -> str:
    """
    Mensaje para usuarios gratuitos explicando el cambio a premium exclusivo
    """
    lines = []
    
    lines.append("🔒 **SISTEMA PREMIUM EXCLUSIVO** 🔒")
    lines.append("")
    lines.append("🎯 **¡Hemos mejorado el sistema!**")
    lines.append("")
    lines.append("Ahora ofrecemos **solo alertas premium** de máxima calidad:")
    lines.append("✨ **5 alertas diarias** de excelencia")
    lines.append("📊 **Probabilidades ajustadas** en tiempo real")
    lines.append("🏥 **Información de alineaciones y lesiones**")
    lines.append("🎯 **Solo las mejores oportunidades**")
    lines.append("💰 **Gestión profesional de bankroll**")
    lines.append("")
    lines.append("💎 **SUSCRIPCIÓN PREMIUM:**")
    lines.append("💵 **$50 USD semanales**")
    lines.append("🏆 **Análisis de nivel institucional**")
    lines.append("📈 **Información en tiempo real**")
    lines.append("🎯 **Solo value bets verificados**")
    lines.append("")
    lines.append("🔥 **¡Obtén acceso inmediato!**")
    lines.append("💬 Contacta para activar tu suscripción")
    lines.append("")
    lines.append("🎁 **PROGRAMA DE REFERIDOS:**")
    lines.append("👥 **3 referidos pagos = 1 semana gratis**")
    lines.append("💰 **10% comisión por cada referido ($5 USD)**")
    
    return "\n".join(lines)


def _get_market_name_spanish(market_key: str) -> str:
    """
    Convierte market_key a nombre en español
    """
    market_names = {
        'h2h': 'Ganador',
        'spreads': 'Hándicap', 
        'totals': 'Totales',
        'moneyline': 'Línea de Dinero',
        'point_spread': 'Diferencia de Puntos',
        'over_under': 'Más/Menos'
    }
    return market_names.get(market_key, market_key.title())


def format_quality_summary_for_admin(quality_summary: Dict) -> str:
    """
    Formato resumen de calidad para el administrador
    """
    lines = []
    
    lines.append("📊 **RESUMEN DE CALIDAD DIARIO**")
    lines.append("")
    lines.append(f"🎯 **Seleccionados:** {quality_summary.get('total_selected', 0)}/5")
    lines.append(f"⭐ **Calidad promedio:** {quality_summary.get('avg_quality_score', 0):.1%}")
    lines.append(f"📊 **Rango:** {quality_summary.get('quality_range', 'N/A')}")
    lines.append(f"🏆 **Nivel:** {quality_summary.get('confidence_level', 'UNKNOWN')}")
    lines.append("")
    
    if quality_summary.get('individual_scores'):
        lines.append("🏅 **Scores individuales:**")
        for score in quality_summary['individual_scores']:
            lines.append(f"  • {score}")
        lines.append("")
    
    if quality_summary.get('top_value_bets'):
        lines.append("🔥 **Top value bets:**")
        for bet in quality_summary['top_value_bets']:
            lines.append(f"  🎯 {bet}")
    
    return "\n".join(lines)


# Función helper para determinar si enviar alerta
def should_send_alert(candidate: Dict, min_quality_threshold: float = 0.6) -> bool:
    """
    Determina si un candidato debe ser enviado como alerta
    """
    quality_score = candidate.get('quality_score', 0.0)
    confidence_score = candidate.get('confidence_score', 0.0)
    current_value = candidate.get('value', 1.0)
    
    # Criterios mínimos
    return (
        quality_score >= min_quality_threshold and
        confidence_score >= 0.6 and
        current_value >= 1.05  # Al menos 5% de valor tras ajustes
    )