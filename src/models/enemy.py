from src.models.entity import Combatant


class Enemy(Combatant):
    """Representa um inimigo ou miniboss."""

    def __init__(self, name, hp, is_miniboss=False):
        super().__init__(name, hp)
        self.is_miniboss = is_miniboss
        self.is_player = False
        self.intent = None
        self.intent_value = 0

    def set_intent(self, intent_type, value):
        """Define a próxima ação planejada pelo inimigo."""
        self.intent = intent_type
        self.intent_value = value
