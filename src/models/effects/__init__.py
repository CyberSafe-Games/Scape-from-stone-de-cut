"""Módulo de efeitos de cartas seguindo o padrão Strategy (Open/Closed Principle)."""
from src.models.effects.base_effect import CardEffect
from src.models.effects.damage_effect import DamageEffect, MultiHitDamageEffect
from src.models.effects.block_effect import BlockEffect
from src.models.effects.buff_effect import StrengthBuffEffect
