from src.models.effects.damage_effect import DamageEffect, MultiHitDamageEffect
from src.models.effects.block_effect import BlockEffect
from src.models.effects.buff_effect import StrengthBuffEffect


class Card:
    """Representa uma carta do baralho com custo, tipo, valor, descrição e efeito polimórfico."""

    def __init__(
        self,
        name,
        cost,
        card_type,
        value,
        description,
        color,
        effect=None,
    ):
        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.value = value
        self.description = description
        self.color = color
        self.effect = effect or self._create_default_effect()

    def _create_default_effect(self):
        """Atribui o efeito padrão adequado caso nenhum tenha sido explicitado."""
        if self.name == "Golpe Duplo":
            return MultiHitDamageEffect(hits=2, action_name="Golpe Duplo")
        if self.card_type == "attack":
            return DamageEffect(action_name=self.name)
        if self.card_type == "skill":
            return BlockEffect(action_name=self.name)
        if self.card_type == "power":
            return StrengthBuffEffect(action_name=self.name)
        return DamageEffect(action_name=self.name)

    def execute(self, user, target, context):
        """Executa a lógica da carta através do seu efeito."""
        return self.effect.apply(self, user, target, context)

    def copy(self):
        """Retorna uma nova instância idêntica da carta."""
        return Card(
            self.name,
            self.cost,
            self.card_type,
            self.value,
            self.description,
            self.color,
            self.effect,
        )
