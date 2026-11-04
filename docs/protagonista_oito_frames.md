# Protagonista com oito frames

Todas as 27 interações usam sequências completas de oito poses: repouso,
dano, soco básico, vitória, as 20 cartas comuns e as três ultimates.
O personagem mantém cabelo, penas, colar e roupas, com ombros estreitos,
braços e pernas finos. A paleta é compartilhada entre todas as poses.

Os sprites ficam em `assets/player/eight_frames`. As folhas originais
geradas pela ferramenta integrada de imagens ficam em `source`, junto ao
manifesto de linhas; os prompts estão em `docs/player_eight_frames_prompts.json`.
O carregamento prioriza as novas sequências e mantém os arquivos anteriores
como fontes históricas. O retrato da HUD acompanha o novo desenho.

As cartas de ataque têm preparação, golpe/lançamento, recuperação e retorno.
O quinto frame coincide com o golpe corpo a corpo (52%) ou lançamento (64%).
Os projéteis continuam independentes, com impacto a 90% da ação. As ultimates
mantêm duração, regras e valores, agora com oito poses e oito efeitos próprios.
O repouso usa um relógio local que recomeça após a ação ou dano, sem saltar
para uma pose arbitrária. Todos os grupos terminam na mesma postura de repouso.

Reexportar os sprites:

```powershell
python -B devtools/prepare_player_eight_frames.py
```

Prévia do combate, sem acessar saves:

```powershell
python -B devtools/preview_player_eight_frames.py
```

Resultados: `docs/protagonista_oito_frames.gif`, `docs/protagonista_oito_frames.png`
e folhas de revisão `docs/player_*_eight_frames.png`.
