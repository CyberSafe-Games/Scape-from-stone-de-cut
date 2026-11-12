# Bosses com doze frames

Os sete bosses usam doze poses em defesa, cura, ataques e ultimates. Álvaro e
Tex contam com as duas fases e a transição entre elas. São 39 sequências de
corpo (468 sprites) e seis camadas de ultimate com doze efeitos cada (72
sprites). Repouso e reação ao dano usam oito poses em
`assets/bosses/eight_frames`.

## Identidade e sequência

As oito poses aprovadas foram conservadas, pixel a pixel, nas posições
1, 3, 4, 6, 7, 9, 10 e 12. Quatro desenhos intermediários ocupam as posições
2, 5, 8 e 11. Foram gerados com a ferramenta integrada de geração de imagens,
usando as próprias animações do jogo como referência.

As fontes estão em `assets/bosses/twelve_frames/<boss>/reference.png` e
`inbetweens.png`. Cada personagem conserva a paleta anterior e o pivô dos pés.
O preparo ajusta as cores dos intermediários por material. A entrada e a
recuperação podem aproveitar poses da referência de repouso do personagem.
`selection.json` registra a origem de cada intermediário selecionado.

A fonte de oito frames permanece em `assets/bosses/eight_frames`. As camadas
especiais ficam em `assets/boss_ultimate_effects/twelve_frames`; os oito efeitos
anteriores também foram conservados nas mesmas posições relativas.

Zanzara mantém o azul escuro, a faixa branca, os detalhes dourados e a onda de
palma para a esquerda. O Carrasco conserva o buff vermelho e as estrelas do cast.
O design e os equipamentos originais dos demais personagens foram preservados.

## Tempos do combate

Os quadros extras subdividem os intervalos existentes. Lançamentos, impactos,
dano, duração das ações, regras dos buffs e troca de fase mantêm seus tempos.
O repouso usa a cadência de `src/config/layout.py`.
Os efeitos de impacto só aparecem na etapa de acerto, inclusive nos saltos do
Carrasco e do Gordofera. Os inimigos comuns usam oito quadros.

## Reprodução e validação

- `python -B devtools/prepare_boss_twelve_frames.py --references` recompõe as referências.
- `python -B devtools/prepare_boss_twelve_frames.py` recompõe os quadros preparados,
  a seleção, os efeitos e as folhas de conferência.
- `python -B devtools/preview_boss_twelve_frames.py` renderiza os encontros reais,
  sem gravar saves; as prévias animadas ficam em `docs/boss_*_twelve_frames.gif`.
- `docs/boss_twelve_frames_prompts.json` contém todos os prompts, com identificação
  da ferramenta utilizada.

Os testes conferem as doze poses alcançáveis, transparência, paleta, estabilidade
de luminosidade, preservação das oito poses antigas, impacto, recuperação e a
transição da dupla. Os testes anteriores de efeitos, combate e campanha seguem
ativos.
