# Carrasco da Vigília

O ponto principal do nível 6 (Pico da Vigília) usa o Carrasco da Vigília. Os encontros normais usam Centauro Vigia e Lutador Mascarado, conforme o bestiário por bioma. O novo chefe aparece também ao repetir a fase, sem alterar os desbloqueios dos saves existentes.

## Regras

- 146 de vida no nível 6, quatro pontos de energia e duas ações por rodada.
- Corte do Carrasco: 13 de dano e custo 1.
- Varredura Escarlate: 17 de dano e custo 2.
- Vigor Escarlate: recupera até 14 de vida e concede +4 de dano por dois turnos completos, incluindo a vez de aplicação. Reaplicar renova a duração, sem acumular o bônus. O Amuleto Dissipador pode remover a aura.
- Execução Escarlate: 24 de dano no oitavo, décimo sexto e demais atos múltiplos de oito.

## Arte e apresentação

24 poses em `assets/carrasco_da_vigilia/`, extraídas das duas referências, com fundo preto removido, orientação à esquerda e canvas uniforme de 448 × 300. Foram preparados idle, dano, três ataques e recuperação, com quatro quadros por grupo. O idle usa respiração suave; ataques possuem durações próprias e a IA aguarda o término da animação.

O verde da recuperação é convertido em vermelho na carga dos sprites, preservando tons neutros da pele, metal e a capa. Uma estrela vermelha pulsa acima da cabeça durante o cast, com partículas ascendentes e um selo discreto no chão. O símbolo desaparece ao encerrar a habilidade.

O fundo `assets/background_pico_da_vigilia.png` foi criado com ImageGen e é selecionado automaticamente em todas as batalhas do bioma 6, incluindo as lutas normais. Cenários e chefes anteriores, bem como as ultimates do jogador, mantêm suas regras.

## Prompt do cenário

Create a production-ready 2D SIDE-VIEW BATTLE BACKGROUND for a dark fantasy pixel-painted turn-based card game. Wide 16:9 composition, 1536x864. Biome PICO DA VIGÍLIA: a windswept ancient South American mountain summit, cracked broad stone plateau, carved indigenous stone watchtower and abandoned signal brazier in the far background, enormous blue-gray serrated peaks and layers of mist-filled valleys, drifting thin snow and lichen, dark red weathered cloth banners at the outer edges recalling an axe-bearing crimson-cloaked guardian. Cold desaturated slate blue, teal-gray rock and muted bronze, faint pale dawn behind heavy clouds with restrained red cloth accents. This is a dramatic and mature painted pixel-art game environment, coherent with a dark tropical-ruins fantasy RPG rather than a European castle. IMPORTANT fighting floor: a continuous flat spacious horizontal stone arena across the middle, ground line 58 percent from the top, clear unobstructed character placement at x20 percent and x80 percent. Cliffs and deep valley are BEHIND the arena, no holes in fighting floor, no props hiding combatants. Upper 15 percent low-contrast sky and background for HUD, lower 27 percent quieter stone foreground for card tray. Intricate crisp rock texture, ancient carvings, worn stairs and dramatic depth. NO characters, NO enemies, NO animals, NO UI, NO cards, NO text, NO letters, NO frames. Full bleed landscape only.

