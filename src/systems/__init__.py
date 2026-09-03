"""Módulo de sistemas e regras do jogo."""
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_enemy, choose_enemy_intent, is_miniboss_level
from src.systems.card_catalog import CARD_POOL, create_starting_deck
