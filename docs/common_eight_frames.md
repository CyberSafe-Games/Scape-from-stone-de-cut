# Inimigos comuns: oito frames

Os 13 habitantes dos encontros normais usam 52 sequências, com oito poses cada
(416 sprites RGBA). Parado, reação de dano, ataques, defesa e cura foram preparados
conforme o kit de cada inimigo. A distribuição por bioma e os valores de combate
foram preservados.

## Integração

- As folhas novas ficam em `assets/enemies/eight_frames/<personagem>`.
  `reference.png` documenta o desenho anterior e `sequence.png` guarda a geração.
  O Mago tem uma revisão separada da conjuração de fogo; o preparo utiliza apenas
  a terceira linha dessa revisão e conserva as outras animações.
- Os quadros têm tela transparente de 448 × 260, pivô comum e paleta compartilhada
  por personagem. Todos olham para a esquerda. A última pose retorna ao repouso.
- O morcego usa os olhos como referência para o pivô, evitando saltos de posição
  quando abre as asas. Seu movimento de voo continua independente da animação.
- Ataques corpo a corpo atingem na quinta pose. Projéteis são lançados na quinta
  pose e seguem trajetórias independentes até o impacto. Vida, texto de dano e
  reação do jogador aguardam esse impacto.
- Slime ganhou reação de dano e projétil separado. Seu retrato mostra o rosto
  completo; o ataque leve do tutorial foi renomeado para acompanhar o salpico.
- Bosses, protagonista e fontes antigas dos inimigos foram conservados.

## Reprodução e conferência

`python -B devtools/prepare_common_eight_frames.py` recompõe os quadros e paletas.
`python -B devtools/preview_common_eight_frames.py` renderiza as ações no combate
real sem gravar saves. A prévia fica em `docs/common_enemies_eight_frames.gif` e
o painel em `docs/common_enemies_in_battle.png`.

Os prompts usados na geração estão em `docs/common_eight_frames_prompts.json`.
O ajuste final do Mago está em `docs/common_mage_fire_revision_prompt.json`.
Os testes em `tests/test_common_eight_frames.py` conferem poses distintas,
transparência, alcance das oito poses, recuperação e sincronização de dano/HUD.
