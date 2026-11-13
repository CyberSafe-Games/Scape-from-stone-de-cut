"""Regras de comércio, independentes de Pygame.

As ofertas usam cartas JÁ existentes no catálogo. Novas cartas podem ser
incluídas futuramente no catálogo e em CARD_PRICES sem alterar a loja.
"""
from copy import deepcopy
from dataclasses import dataclass

from src.systems.card_catalog import AVAILABLE_CARD_POOL
from src.systems.save_manager import HEALTH_UPGRADE_AMOUNT, HEALTH_UPGRADE_LIMIT, SaveError

HEALTH_UPGRADE_PRICE = 50

# Preços iniciais, editáveis; não criam novas cartas nem dependem de novas artes.
CARD_PRICES = {card.name: 25 + card.cost * 15 for card in AVAILABLE_CARD_POOL}

@dataclass(frozen=True)
class ShopResult:
    success: bool
    message: str
    amount: int = 0


# Fonte única de nomes, tipos e descrições: modelo real do jogo.
CARD_OFFERS = {card.name: card for card in AVAILABLE_CARD_POOL if card.name in CARD_PRICES}


def _commit_progress(save_manager, data, mutate):
    """Garante que falha de gravação não desconte saldo apenas em memória."""
    original = deepcopy(data["progresso"])
    try:
        mutate(data["progresso"])
        save_manager.save(data)
    except (OSError, ValueError, TypeError, SaveError):
        data["progresso"] = original
        return False
    return True


def purchase_health_upgrade(save_manager, data):
    """Aumenta o limite de vida sem alterar a vida atual."""
    progress = data["progresso"]
    purchases = progress["melhorias_vida_run"]
    if purchases >= HEALTH_UPGRADE_LIMIT:
        return ShopResult(False, "Limite de três melhorias de vida por run atingido.")
    if progress["moedas"] < HEALTH_UPGRADE_PRICE:
        return ShopResult(False, "Moedas insuficientes para comprar a melhoria.")

    def mutate(progress):
        progress["moedas"] -= HEALTH_UPGRADE_PRICE
        progress["melhorias_vida_run"] += 1

    if not _commit_progress(save_manager, data, mutate):
        return ShopResult(False, "Não foi possível salvar a compra. Nada foi cobrado.")
    return ShopResult(True, f"+{HEALTH_UPGRADE_AMOUNT} de vida máxima!", HEALTH_UPGRADE_AMOUNT)


def purchase_card(save_manager, data, card_name):
    """Adiciona uma carta do catálogo ao baralho persistente mediante pagamento."""
    if card_name not in CARD_OFFERS:
        return ShopResult(False, "Esta carta ainda não está disponível na loja.")
    price = CARD_PRICES[card_name]
    if card_name in data["progresso"].get("cartas_colecao", []):
        return ShopResult(False, "Este tipo de carta já está na sua coleção.")
    if data["progresso"]["moedas"] < price:
        return ShopResult(False, "Moedas insuficientes para comprar esta carta.")
    def mutate(progress):
        progress["moedas"] -= price
        progress["cartas_colecao"].append(card_name)
    if not _commit_progress(save_manager, data, mutate):
        return ShopResult(False, "Não foi possível salvar a compra. Nada foi cobrado.")
    return ShopResult(True, f"{card_name} adicionada à coleção! Equipe na mochila.")
