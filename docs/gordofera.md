# Gordofera — guardião do Pântano Abissal

Gordofera ocupa o confronto principal do nível 4, completando o elenco dos
sete chefes territoriais. Os encontros comuns continuam com Putrefato do
Pântano e Crocodilo Abissal; Zanzara permanece no Santuário de Pedra.

O desenho conserva a fera corpulenta das referências: rosto com presas,
pelagem castanha, chifres pretos, capa verde-escura bordada em dourado,
camisa clara, calça escura rasgada, cinto e garras. Todas as poses encaram
a esquerda, com transparência real e sem margens brancas. Uma paleta
compartilhada e o alinhamento dos pés mantêm as poses consistentes.

São 56 sprites: repouso, dano, garras, rugido com investida, cabeçada,
guarda e ultimate, cada ação com oito frames. A guarda não ataca nem cura.
A ultimate tem animação própria de salto e impacto, com efeitos separados
de selo, onda de lama, explosão de terra e anel de poeira.

## Kit

116 de vida, 4 de energia e duas ações por turno completo.

| Ação | Efeito | Peso |
| --- | --- | --- |
| Garras Dilacerantes | 9 de dano e Sangramento por 2 turnos (4 de dano no primeiro ataque do alvo por turno) | 35% |
| Rugido Feroz | Investida corpo a corpo, 11 de dano | 25% |
| Cabeçada Brutal | 14 de dano | 25% |
| Guarda Ferrenha | 10 de Escudo, seguindo a duração existente de 2 turnos | 15% |
| Abalo Abissal | 21 de dano, especial a cada 8 ações | Especial |

O Abalo dura 2700 ms e atinge a 64% da sequência: a sexta pose é a queda
das mãos ao chão, sincronizada com vida, flash e texto do dano. A animação
volta à postura de repouso antes da próxima ação. O salto não cria outra
fase de combate e não exige migração de saves.

## Arquivos

- Sprites e fontes: `assets/bosses/eight_frames/gordofera`.
- Efeitos da ultimate: `assets/boss_ultimate_effects/gordofera`.
- Fontes originais preservadas em `source/original_poses.png` e `source/original_attacks.png`.
- Ferramenta integrada de geração de imagens; prompts: `docs/gordofera_prompts.json`.
- Exportação: `python -B devtools/prepare_swamp_boss.py`.
- Prévia sem saves: `python -B devtools/preview_swamp_boss.py`.
- Resultado: `docs/gordofera_em_acao.gif` e `docs/gordofera_em_combate.png`.
