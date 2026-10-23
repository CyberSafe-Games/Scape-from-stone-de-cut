import random


class DeckManager:
    """Gerencia as pilhas de cartas durante o combate: compra, mão e descarte.

    Segue o princípio da Responsabilidade Única (SRP).
    """

    def __init__(self, initial_cards=None):
        self.deck = [c.copy() for c in (initial_cards or [])]
        self.draw_pile = []
        self.hand = []
        self.discard_pile = []

    def start_combat(self):
        """Prepara o baralho no início de um novo combate."""
        self.draw_pile = [card.copy() for card in self.deck]
        random.shuffle(self.draw_pile)
        self.hand = []
        self.discard_pile = []

    def draw_cards(self, amount):
        """Puxa cartas da pilha de compra para a mão, reembaralhando o descarte se necessário."""
        for _ in range(amount):
            if not self.draw_pile:
                if not self.discard_pile:
                    break
                self.draw_pile = self.discard_pile[:]
                random.shuffle(self.draw_pile)
                self.discard_pile.clear()

            if self.draw_pile:
                self.hand.append(self.draw_pile.pop())

    def refill_hand(self, target_size):
        """Completa a mão sem descartar as cartas não utilizadas.

        target_size é o alvo de compra do turno, não uma capacidade rígida:
        efeitos especiais ainda podem conceder cartas extras.
        """
        amount = max(0, int(target_size) - len(self.hand))
        before = len(self.hand)
        self.draw_cards(amount)
        return len(self.hand) - before

    def has_replacement_for(self, index):
        """Há carta diferente da selecionada disponível para troca imediata?"""
        return 0 <= index < len(self.hand) and bool(self.draw_pile or self.discard_pile)

    def swap_card(self, index):
        """Descarta uma carta e compra outra, sem voltar a comprar a própria carta.

        A carta escolhida só entra no descarte *após* a reposição, inclusive
        quando é necessário reembaralhar o descarte para comprar.
        """
        if not self.has_replacement_for(index):
            return None
        removed = self.hand.pop(index)
        before = len(self.hand)
        self.draw_cards(1)
        if len(self.hand) == before:
            # Garantia defensiva para não perder uma carta sem reposição.
            self.hand.insert(index, removed)
            return None
        replacement = self.hand.pop()
        self.hand.insert(index, replacement)
        self.discard_pile.append(removed)
        return removed, replacement

    def discard_card(self, index):
        """Move uma carta específica da mão para a pilha de descarte."""
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            self.discard_pile.append(card)
            return card
        return None

    def discard_hand(self):
        """Move todas as cartas da mão para o descarte (ex: ao fim de turno)."""
        self.discard_pile.extend(self.hand)
        self.hand.clear()

    def add_to_deck(self, card):
        """Adiciona permanentemente uma carta ao baralho do jogador (recompensa)."""
        self.deck.append(card.copy())
