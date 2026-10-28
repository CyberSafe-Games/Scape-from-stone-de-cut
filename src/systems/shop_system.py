"""Regras de comércio e cura, independentes de Pygame.

As ofertas usam cartas JÁ existentes no catálogo. Novas cartas podem ser
incluídas futuramente no catálogo e em CARD_PRICES sem alterar a loja.
"""
from copy import deepcopy
from dataclasses import dataclass

from src.systems.card_catalog import CARD_POOL
from src.systems.save_manager import SaveError

HEAL_PRICE = 50  # Saldo em moedas. Ajustável para balanceamento.
HEAL_AMOUNT = 15
HEAL_PURCHASE_LIMIT = 3  # Por RUN/save, NÃO por território.
MAX_PLAYER_HP = 60

# Preços iniciais, editáveis; não criam novas cartas nem dependem de novas artes.
CARD_PRICES = {card.name: 25 + card.cost * 15 for card in CARD_POOL}

@dataclass(frozen=True)
class ShopResult:
    success: bool
    message: str
    amount: int = 0


# Fonte única de nomes, tipos e descrições: modelo real do jogo.
CARD_OFFERS = {card.name: card for card in CARD_POOL if card.name in CARD_PRICES}


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


def purchase_healing(save_manager, data):
    """Compra +15 HP, até três vezes por RUN, preservando limite de 60 HP."""
    p = data["progresso"]
    purchases = p.get("curas_compradas_run", 0)
    if purchases >= HEAL_PURCHASE_LIMIT:
        return ShopResult(False, "Limite de três curas por RUN atingido.")
    if p["vida"] >= MAX_PLAYER_HP:
        return ShopResult(False, "A vida já está no máximo.")
    if p["moedas"] < HEAL_PRICE:
        return ShopResult(False, "Moedas insuficientes para comprar a cura.")
    recovered = min(HEAL_AMOUNT, MAX_PLAYER_HP - p["vida"])
    def mutate(progress):
        progress["moedas"] -= HEAL_PRICE
        progress["vida"] += recovered
        progress["curas_compradas_run"] += 1
    if not _commit_progress(save_manager, data, mutate):
        return ShopResult(False, "Não foi possível salvar a compra. Nada foi cobrado.")
    return ShopResult(True, f"Cura adquirida! +{recovered} de vida.", recovered)


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
