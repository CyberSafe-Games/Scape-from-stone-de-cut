# Protagonista com doze frames

Soco básico, vitória, vinte cartas e três ultimates usam doze poses. São 300
sprites de corpo e 36 efeitos de ultimate. Repouso e reação ao dano usam oito
poses em `assets/player/eight_frames`.
O protagonista mantém a silhueta magrela, o rosto, as penas, as roupas e a paleta
aprovados. Olha para a direita e conserva o pivô dos pés e a transparência.

## Arte e integração

Os quadros estão em `assets/player/twelve_frames`. As oito poses anteriores foram
conservadas pixel a pixel nas posições 1, 3, 4, 6, 7, 9, 10 e 12. Os intermediários
ocupam 2, 5, 8 e 11; são desenhos novos, sem misturar imagens ou duplicar quadros.
As fontes em `source` foram geradas pela ferramenta integrada de geração de imagens.
`selection.json` registra as poses intermediárias selecionadas para as ações.

Todos os prompts estão em `docs/player_twelve_frames_prompts.json`. O preparo usa
a paleta anterior e ajusta as cores por material.
Os arquivos em `assets/player/eight_frames` permanecem disponíveis
para reprodução e comparação da identidade.

## Movimento e efeitos

- Os tempos das ações, o lançamento dos projéteis e os impactos foram preservados.
- Repouso e vitória usam a cadência de `src/config/layout.py`.
- O soco básico usa a sequência completa de preparação, golpe e recuperação.
- Os efeitos de Mana Ancestral, Forças Ancestrais e Rugido da Floresta também têm
  doze desenhos. A dissipação do rugido começa no impacto, com voo para a direita.
- O balanceamento, as cartas, os chefes e os inimigos comuns mantêm suas regras.

## Reprodução e validação

`python -B devtools/prepare_player_twelve_frames.py --references` recompõe as
referências. Sem opções, o mesmo script recompõe os sprites e as folhas de
conferência. `--qa` gera somente as folhas dos intermediários selecionados.

`python -B devtools/preview_player_twelve_frames.py` renderiza as 27 interações
em combate sem ler nem gravar saves. Resultados:

- `docs/protagonista_doze_frames.gif`: prévia animada de todas as ações;
- `docs/protagonista_doze_frames.png`: painel de interações;
- `docs/player_new_intermediates_1.png` até `_3.png`: poses novas selecionadas;
- `docs/player_ultimate_effects_twelve_frames.png`: camadas das três ultimates.

Os testes verificam as doze poses, recuperação, transparência, paleta, silhueta,
brilho estável, preservação dos oito desenhos anteriores e sincronização entre
conjuração, projétil, impacto e dissipação.

Validação em 05/11/2026: suíte completa com 344 testes e 917 subtestes aprovados.
As animações e ultimates também passaram na revisão específica final
(14 testes e 69 subtestes), incluindo o refinamento das poses das armas.
