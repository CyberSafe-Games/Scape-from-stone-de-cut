# Intenções dos inimigos

Os inimigos planejam a rodada antes do turno do jogador: uma ação nos
encontros normais e duas nos chefes. A segunda ação executa o plano já
anunciado, sem novo sorteio. A energia é reservada entre as duas ações e
o especial continua ocorrendo a cada oito ações; quando for a segunda
ação da rodada, ele já aparece no segundo ícone.

A HUD mostra ícones com ordem, valor previsto e destaque dourado para
ultimates. A ação atual é destacada; a anterior fica apagada com confirmação
de conclusão. Ao fim da rodada, as próximas intenções substituem as antigas.
Os ícones são desenhados e armazenados em cache pela interface do Pygame,
sem exigir novos arquivos de imagem.

Passar o mouse revela o nome da habilidade, sua ordem, estado e descrição.
Ataques consideram Força, aura, Fraqueza e Fragilidade do jogador. O valor
é mostrado antes de Escudo e Totem. Se a primeira ação aplicar um bônus,
a previsão da segunda já o considera. Cura, defesa e buffs têm descrições
próprias, incluindo durações e regras de reaplicação. A consulta e o desenho
não alteram a luta nem consomem sorteios aleatórios.

Alterações principais: `Enemy.action_plan`, `choose_next_action`,
`src/systems/enemy_intents.py` e `src/ui/enemy_intent_view.py`.
Não há alteração no formato dos saves: o plano é refeito ao iniciar a luta,
assim como o estado do combate já era reiniciado anteriormente.

Prévia: `python -B devtools/preview_enemy_intents.py`.
Resultados: `docs/intencoes_preview.png` e `docs/intencoes_*.png`.
