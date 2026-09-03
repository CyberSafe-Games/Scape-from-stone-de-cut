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
