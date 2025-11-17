"""
payments/premium_integration.py - Integración del sistema de referidos con pagos Premium

Maneja:
- Procesamiento de pagos Premium con comisiones automáticas
- Notificaciones a referrers cuando sus referidos pagan
- Historial de transacciones y auditoría
- Validación de anti-fraude
- Activación automática de Premium y semanas gratis
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple

from referrals import ReferralSystem
from data.users import UsersManager, PREMIUM_PRICE_USD

logger = logging.getLogger(__name__)


class PremiumPaymentProcessor:
    """
    Procesa pagos Premium e integra con sistema de referidos
    """
    
    def __init__(
        self,
        referral_system: ReferralSystem,
        user_manager: UsersManager,
        notifier=None  # TelegramNotifier opcional
    ):
        """
        Args:
            referral_system: Sistema de referidos
            user_manager: Gestor de usuarios
            notifier: Notificador de Telegram (opcional)
        """
        self.referral_system = referral_system
        self.user_manager = user_manager
        self.notifier = notifier
    
    def process_payment(
        self,
        user_id: str,
        amount_usd: float,
        weeks: int = 1,
        payment_method: str = "manual",
        transaction_id: Optional[str] = None
    ) -> Dict:
        """
        Procesa un pago Premium completo con todas las integraciones
        
        Args:
            user_id: ID del usuario que paga
            amount_usd: Monto pagado en USD
            weeks: Número de semanas de Premium
            payment_method: Método de pago utilizado
            transaction_id: ID de transacción externa (opcional)
            
        Returns:
            Dict con resultado completo del procesamiento
        """
        logger.info(
            f"Procesando pago Premium: user={user_id}, amount=${amount_usd}, "
            f"weeks={weeks}, method={payment_method}"
        )
        
        result = {
            'success': False,
            'user_id': user_id,
            'amount': amount_usd,
            'weeks': weeks,
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'errors': []
        }
        
        try:
            # 1. Validar usuario existe
            user = self.user_manager.get_user(user_id)
            if not user:
                result['errors'].append('Usuario no encontrado')
                logger.error(f"Usuario {user_id} no existe")
                return result
            
            # 2. Validar monto
            expected_amount = PREMIUM_PRICE_USD * weeks
            if abs(amount_usd - expected_amount) > 0.01:  # Tolerancia de 1 centavo
                result['errors'].append(
                    f'Monto incorrecto. Esperado: ${expected_amount:.2f}, '
                    f'Recibido: ${amount_usd:.2f}'
                )
                logger.warning(f"Monto incorrecto para {user_id}")
                # Continuar de todas formas (en caso de descuentos)
            
            # 3. Activar Premium para el usuario
            premium_result = self._activate_premium(user, weeks)
            result['premium_activated'] = premium_result
            
            # 4. Procesar comisión para referrer (si existe)
            referrer_result = self.referral_system.process_premium_payment(
                user_id=user_id,
                amount_usd=amount_usd,
                payment_method=payment_method
            )
            result['referral_reward'] = referrer_result
            
            # 5. Si se otorgó recompensa, notificar al referrer
            if referrer_result.get('reward_granted'):
                # Guardar para notificar después (necesita async context)
                result['notify_referrer'] = referrer_result
            
            # 6. Notificar al usuario del pago exitoso
            if self.notifier:
                # Guardar para notificar después (necesita async context)
                result['notify_user'] = premium_result
            
            # 7. Verificar anti-fraude si es nuevo usuario
            if user.total_bets == 0:  # Usuario completamente nuevo
                fraud_analysis = self.referral_system.detect_fraud(user_id)
                if fraud_analysis['risk_level'] in ['HIGH', 'MEDIUM']:
                    result['fraud_alert'] = fraud_analysis
                    logger.warning(
                        f"Alerta de fraude para {user_id}: "
                        f"nivel {fraud_analysis['risk_level']}"
                    )
            
            result['success'] = True
            logger.info(f"Pago procesado exitosamente para {user_id}")
            
        except Exception as e:
            result['errors'].append(f'Error procesando pago: {str(e)}')
            logger.error(f"Error procesando pago de {user_id}: {e}", exc_info=True)
        
        return result
    
    def _activate_premium(self, user, weeks: int) -> Dict:
        """
        Activa o extiende Premium para un usuario
        
        Args:
            user: Objeto User
            weeks: Número de semanas a activar
            
        Returns:
            Dict con información de activación
        """
        current_date = datetime.now(timezone.utc)
        days = weeks * 7
        
        # Si ya tiene suscripción activa, extender desde fecha actual
        if user.suscripcion_fin:
            expiry_date = datetime.fromisoformat(user.suscripcion_fin)
            if expiry_date > current_date:
                # Extender desde fecha de expiración existente
                new_expiry = expiry_date + timedelta(days=days)
                was_active = True
            else:
                # Ya expiró, empezar desde ahora
                new_expiry = current_date + timedelta(days=days)
                was_active = False
        else:
            # Primera activación
            new_expiry = current_date + timedelta(days=days)
            was_active = False
        
        # Actualizar usuario
        old_expiry = user.suscripcion_fin
        user.suscripcion_fin = new_expiry.isoformat()
        user.nivel = "premium"
        
        # Guardar cambios
        self.user_manager.update_user(user)
        
        return {
            'user_id': user.chat_id,
            'was_active': was_active,
            'old_expiry': old_expiry,
            'new_expiry': new_expiry.isoformat(),
            'weeks_added': weeks,
            'total_days': days
        }
    
    async def _notify_referrer_reward(self, referrer_result: Dict):
        """Notifica al referrer que ganó una recompensa"""
        if not self.notifier:
            return
        
        try:
            referrer_id = referrer_result['referrer_id']
            commission = referrer_result['commission']
            new_balance = referrer_result['new_balance']
            paid_referrals = referrer_result['paid_referrals']
            free_week = referrer_result.get('free_week_granted', False)
            
            message = (
                "FELICIDADES! Ganaste una recompensa!\n\n"
                f"Uno de tus referidos pagó Premium y ganaste ${commission:.2f} USD!\n\n"
                f"Tu saldo actual: ${new_balance:.2f}\n"
                f"Referidos que pagaron: {paid_referrals}\n"
            )
            
            if free_week:
                weeks_earned = referrer_result.get('free_weeks_total', 0)
                message += (
                    f"\n"
                    f"BONUS! También ganaste 1 semana Premium GRATIS!\n"
                    f"Total semanas gratis: {weeks_earned}\n"
                    f"Usa /canjear para activarla.\n"
                )
            
            message += (
                f"\n"
                f"Usa /referidos para ver tus estadísticas.\n"
                f"Usa /retirar [monto] para solicitar retiro."
            )
            
            await self.notifier.send_message(referrer_id, message)
            
            logger.info(f"Notificación de recompensa enviada a {referrer_id}")
            
        except Exception as e:
            logger.error(f"Error notificando recompensa: {e}")
    
    async def _notify_payment_success(self, user_id: str, premium_result: Dict):
        """Notifica al usuario que su pago fue exitoso"""
        if not self.notifier:
            return
        
        try:
            new_expiry = datetime.fromisoformat(premium_result['new_expiry'])
            weeks = premium_result['weeks_added']
            
            message = (
                "PAGO EXITOSO!\n\n"
                f"Tu suscripción Premium ha sido activada por {weeks} semana(s).\n\n"
                f"Válida hasta: {new_expiry.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                "Ahora recibirás hasta 5 alertas diarias de máxima calidad con:\n"
                "- Análisis profesional con Kelly Criterion\n"
                "- Pronósticos con IA y datos en tiempo real\n"
                "- Seguimiento de resultados y ROI\n"
                "- Soporte prioritario\n\n"
                "Recuerda compartir tu código de referido y ganar recompensas!\n"
                "Usa /referidos para ver tu enlace."
            )
            
            await self.notifier.send_message(user_id, message)
            
            logger.info(f"Notificación de pago enviada a {user_id}")
            
        except Exception as e:
            logger.error(f"Error notificando pago: {e}")
    
    def verify_referral_chain(self, user_id: str) -> Dict:
        """
        Verifica la integridad de la cadena de referidos
        
        Args:
            user_id: ID del usuario a verificar
            
        Returns:
            Dict con análisis de la cadena
        """
        result = {
            'user_id': user_id,
            'is_valid': True,
            'depth': 0,
            'chain': [],
            'issues': []
        }
        
        # Obtener stats del usuario
        stats = self.referral_system.get_user_stats(user_id)
        if not stats:
            result['is_valid'] = False
            result['issues'].append('Usuario no registrado en sistema de referidos')
            return result
        
        # Verificar cadena hacia arriba (quien lo refirió)
        current_id = user_id
        visited = set()
        
        while current_id:
            if current_id in visited:
                # Ciclo detectado!
                result['is_valid'] = False
                result['issues'].append(f'Ciclo detectado en {current_id}')
                break
            
            visited.add(current_id)
            
            # Obtener referrer
            user_data = self.referral_system.referrals.get(current_id)
            if not user_data:
                break
            
            referrer_id = user_data.get('referrer_id')
            if referrer_id:
                result['chain'].append({
                    'user': current_id,
                    'referred_by': referrer_id,
                    'depth': result['depth']
                })
                result['depth'] += 1
                current_id = referrer_id
            else:
                # Llegó al top de la cadena
                break
        
        # Verificar límite de profundidad (evitar cadenas demasiado largas)
        if result['depth'] > 10:
            result['is_valid'] = False
            result['issues'].append('Cadena demasiado profunda (>10 niveles)')
        
        return result
    
    def get_payment_history(self, user_id: str, limit: int = 10) -> list:
        """
        Obtiene historial de pagos de un usuario
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de transacciones
            
        Returns:
            Lista de transacciones de pago
        """
        payments = []
        
        for tx in self.referral_system.transactions:
            # Solo transacciones de este usuario que sean pagos
            if tx['user_id'] == user_id:
                if tx['type'] in ['premium_payment', 'free_week_redeemed']:
                    payments.append(tx)
        
        # Ordenar por fecha descendente
        payments.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return payments[:limit]
    
    def generate_invoice(
        self,
        user_id: str,
        amount: float,
        weeks: int,
        payment_method: str = "manual"
    ) -> Dict:
        """
        Genera un "invoice" (factura) para pago Premium
        
        Args:
            user_id: ID del usuario
            amount: Monto en USD
            weeks: Número de semanas
            payment_method: Método de pago
            
        Returns:
            Dict con información de la factura
        """
        invoice_id = f"INV-{user_id[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        user = self.user_manager.get_user(user_id)
        
        invoice = {
            'invoice_id': invoice_id,
            'user_id': user_id,
            'username': user.chat_id if user else 'Unknown',
            'amount_usd': amount,
            'weeks': weeks,
            'payment_method': payment_method,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'pending',
            'description': f'Premium Subscription - {weeks} week(s)',
            'items': [
                {
                    'description': f'Premium subscription ({weeks} week)',
                    'unit_price': PREMIUM_PRICE_USD,
                    'quantity': weeks,
                    'total': amount
                }
            ]
        }
        
        return invoice


# Funciones helper
def calculate_premium_price(weeks: int, discount_percent: float = 0.0) -> float:
    """
    Calcula el precio total de Premium con descuento opcional
    
    Args:
        weeks: Número de semanas
        discount_percent: Porcentaje de descuento (0-100)
        
    Returns:
        float: Precio total en USD
    """
    base_price = PREMIUM_PRICE_USD * weeks
    
    if discount_percent > 0:
        discount_amount = base_price * (discount_percent / 100)
        return base_price - discount_amount
    
    return base_price


def format_payment_receipt(payment_result: Dict) -> str:
    """
    Formatea un recibo de pago para mostrar al usuario
    
    Args:
        payment_result: Resultado del procesamiento de pago
        
    Returns:
        str: Recibo formateado
    """
    lines = [
        "RECIBO DE PAGO",
        "="*50,
        "",
        f"Usuario: {payment_result['user_id']}",
        f"Monto: ${payment_result['amount']:.2f} USD",
        f"Semanas: {payment_result['weeks']}",
        f"Método: {payment_result['payment_method']}",
        f"Fecha: {payment_result['timestamp'][:19]}",
        ""
    ]
    
    if payment_result.get('transaction_id'):
        lines.append(f"ID Transacción: {payment_result['transaction_id']}")
        lines.append("")
    
    premium = payment_result.get('premium_activated', {})
    if premium:
        expiry = datetime.fromisoformat(premium['new_expiry'])
        lines.extend([
            "PREMIUM ACTIVADO:",
            f"  Válido hasta: {expiry.strftime('%Y-%m-%d %H:%M UTC')}",
            f"  Días totales: {premium['total_days']}",
            ""
        ])
    
    referral = payment_result.get('referral_reward', {})
    if referral and referral.get('reward_granted'):
        lines.extend([
            "RECOMPENSA PARA REFERRER:",
            f"  Referrer: {referral['referrer_id']}",
            f"  Comisión: ${referral['commission']:.2f}",
            f"  Nuevo saldo: ${referral['new_balance']:.2f}",
            ""
        ])
    
    if payment_result.get('errors'):
        lines.extend([
            "ERRORES:",
            *[f"  - {err}" for err in payment_result['errors']],
            ""
        ])
    
    lines.append("="*50)
    
    return "\n".join(lines)


# Ejemplo de uso
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from referrals import ReferralSystem
    from data.users import UserManager
    
    # Inicializar sistemas
    ref_system = ReferralSystem("data/test_referrals.json")
    user_manager = UserManager("data/test_users.json")
    
    # Crear procesador
    processor = PremiumPaymentProcessor(ref_system, user_manager)
    
    # Simular pago
    result = processor.process_payment(
        user_id="user_123",
        amount_usd=50.0,
        weeks=1,
        payment_method="PayPal",
        transaction_id="PAYPAL-ABC123"
    )
    
    # Mostrar resultado
    print(format_payment_receipt(result))
    
    # Verificar cadena de referidos
    chain = processor.verify_referral_chain("user_123")
    print(f"\nCadena de referidos válida: {chain['is_valid']}")
    print(f"Profundidad: {chain['depth']}")
