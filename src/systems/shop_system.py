"""Regras de comércio, independentes de Pygame.

As ofertas usam cartas JÁ existentes no catálogo. Novas cartas podem ser
incluídas futuramente no catálogo e em CARD_PRICES sem alterar a loja.
"""
from dataclasses import dataclass

from src.systems.card_catalog import AVAILABLE_CARD_POOL
from src.systems.save_manager import player_max_hp
from src.config.shop_balance import HEAL_AMOUNT, HEAL_PRICES, HEAL_LIMIT

def next_heal_price(progress):
    """Retorna o preço da próxima cura ou None quando a oferta esgotou."""
    count = progress.get('curas_loja_run', 0)
    if type(count) is not int or not 0 <= count <= HEAL_LIMIT:
        raise ValueError('Contador de curas da loja inválido.')
    return HEAL_PRICES[count] if count < HEAL_LIMIT else None

# Preços iniciais, editáveis; não criam novas cartas nem dependem de novas artes.
from src.systems.roguelite import CARD_PRICES

@dataclass(frozen=True)
class ShopResult:
    success: bool
    message: str
    amount: int = 0


# Fonte única de nomes, tipos e descrições: modelo real do jogo.
CARD_OFFERS = {card.name: card for card in AVAILABLE_CARD_POOL if card.name in CARD_PRICES}


def _commit_progress(save_manager, data, mutate):
    """Garante que falha de gravação não desconte saldo apenas em memória."""
    from src.systems.roguelite import transact
    def operation():
        mutate(data['progresso'])
        return 'Compra gravada.'
    return transact(save_manager, data, operation)[0]


def purchase_heal(save_manager, data):
    """Recupera vida atual na loja, sem alterar o máximo nem o perfil."""
    progress = data["progresso"]
    if progress.get('estado', 'ativa') != 'ativa' or progress.get('combat_snapshot'):
        return ShopResult(False, 'Conclua o combate de uma run ativa antes de comprar.')
    if progress['vida'] <= 0:
        return ShopResult(False, 'Uma run encerrada não pode ser recuperada pela loja.')
    price = next_heal_price(progress)
    if price is None:
        return ShopResult(False, 'As três curas desta run foram usadas. Oferta esgotada.')
    amount = min(HEAL_AMOUNT, player_max_hp(progress) - progress['vida'])
    if amount <= 0:
        return ShopResult(False, 'Sua vida já está cheia. Nada foi cobrado.')
    if progress["moedas"] < price:
        return ShopResult(False, "Moedas insuficientes para comprar a cura.")

    def mutate(progress):
        progress["moedas"] -= price
        progress['vida'] += amount
        progress['curas_loja_run'] = progress.get('curas_loja_run', 0) + 1

    if not _commit_progress(save_manager, data, mutate):
        return ShopResult(False, "Não foi possível salvar a compra. Nada foi cobrado.")
    return ShopResult(True, f'+{amount} de vida recuperada!', amount)


def purchase_card(save_manager, data, card_name):
    """Adiciona uma carta do catálogo ao baralho persistente mediante pagamento."""
    if data['progresso'].get('estado', 'ativa') != 'ativa' or data['progresso'].get('combat_snapshot'):
        return ShopResult(False, 'Conclua o combate de uma run ativa antes de comprar.')
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
