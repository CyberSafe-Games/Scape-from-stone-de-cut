# Intenções dos inimigos

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Comuns anunciam uma ação, chefes duas em ordem; a segunda executa o plano já
mostrado, sem novo sorteio. A previsão incorpora bônus da primeira ação.
O especial continua acontecendo a cada oito ações.

Ícones ficam no canto superior direito acima do inimigo, com ordem/valor e
destaque do especial. Arte completa cabe inteira e centralizada no slot.
Hover com arte mostra **somente a própria carta ampliada**: x central e y≈43%,
limitada às bordas, acima da arena e afastada da mão. Sem painel lateral de
texto e sem captura de eventos. Sem arte completa há ficha textual única.

Danos previstos são anteriores a Escudo/Totem e consideram Força, aura,
Fraqueza e Vulnerável. Cura/defesa/buffs usam efeitos reais. Desenho e consulta
não consomem energia nem sorteios. O snapshot de combate preserva o estado.

Fontes: Enemy.action_plan, enemy_intents.py e enemy_intent_view.py.
Artes em assets/intent_art/; testes em test_enemy_intents.
Ver [estado_atual.md](estado_atual.md).
