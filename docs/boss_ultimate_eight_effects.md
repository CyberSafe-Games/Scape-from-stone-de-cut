# Efeitos das ultimates com oito frames

Guardião da Pedra, Goblin Nerd, Corpo Seco, Carrasco da Vigília, Zanzara e
Gordofera agora usam oito sprites de efeito por ultimate. As quatro chaves
anteriores permanecem intactas nas posições 1, 3, 5 e 7. Os frames 2, 4,
6 e 8 são desenhos inéditos gerados para as transições e a dissipação final.
Não são cópias ou simples repetições das imagens existentes.

O corpo dos personagens mantém seus oito frames e seu design. Dano,
duração, lançamento, momento do impacto e intervalos das habilidades
continuam iguais. O seletor de efeitos separa carga, ataque e dissipação.
Nos ataques de impacto no chão, a explosão só aparece no instante do dano;
nos projéteis e giros, a forma mais intensa acompanha a aproximação.
Selos, partículas e rastros continuam animados pelo jogo.

Álvaro e Tex já usam efeitos contínuos de arcos e partículas desenhados
diretamente pelo jogo, sem uma sequência limitada a quatro sprites. Esses
efeitos e as animações de oito poses das duas fases foram preservados.

## Arquivos e reprodução

- Assets finais: `assets/boss_ultimate_effects/eight_frames/<boss>/effect_1.png` até `effect_8.png`.
- As fontes `reference.png` e `intermediates.png` ficam junto aos sprites.
- Prompts da ferramenta integrada de geração: `docs/boss_ultimate_eight_effects_prompts.json`.
- Exportação: `python -B devtools/prepare_boss_ultimate_eight_effects.py`.
- Prévia no combate: `python -B devtools/preview_boss_ultimate_eight_effects.py`.
- Prévia animada: `docs/boss_ultimate_effects_eight_frames.gif`.

Os arquivos originais em `assets/boss_ultimate_effects/<boss>` continuam
disponíveis para comparação. O carregador usa a sequência nova completa
quando presente e mantém compatibilidade com as quatro camadas antigas.
