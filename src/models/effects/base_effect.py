from abc import ABC, abstractmethod


class CardEffect(ABC):
    """Interface abstrata para efeitos de cartas.

    Permite adicionar novas mecânicas (envenenamento, cura, etc.) sem alterar
    o motor de combate existente (Open/Closed Principle).
    """

    @abstractmethod
    def apply(self, card, user, target, context):
        """Executa a lógica do efeito.

        :param card: A carta sendo jogada.
        :param user: Quem jogou a carta (Player).
        :param target: Alvo da ação (Enemy).
        :param context: Referência ou callback do sistema de combate/animação.
        :return: Dicionário ou objeto com o resultado da aplicação.
        """
        pass
