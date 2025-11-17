"""
referrals/__init__.py - Módulo de sistema de referidos
"""

from .referral_system import (
    ReferralSystem,
    format_referral_stats
)

__all__ = [
    'ReferralSystem',
    'format_referral_stats'
]
