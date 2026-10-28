# Guardião da Pedra e cenários dos biomas

O confronto principal da fase 1 (Pedra do Corte) agora usa o Guardião da Pedra. Os três encontros comuns continuam sorteando Slime e Vinimuth, e o tutorial mantém seu Slime didático. Saves existentes mantêm o progresso; o novo chefe aparece ao jogar ou repetir o ponto principal.

## Chefe

- 78 de vida no nível 1; miniboss com duas ações por rodada e quatro pontos de energia.
- Golpe de Garras: 7 de dano; Pele Rochosa: 8 de Escudo; Vigor Selvagem: recupera até 8 de vida.
- Rugido Espiritual: 14 de dano à distância na oitava, décima sexta e demais ações múltiplas de oito. A cabeça de urso se desprende da animação e viaja até o herói; o chefe fica em seu lugar e o flash aguarda o impacto.
- 24 quadros em PNG RGBA, virados à esquerda: idle, atk1, atk2, def, healer2 e dano, quatro quadros por grupo. Canvas uniforme de 448 × 280, pivô nos pés e escala corporal compatível com o herói. Arte e projétil extraídos das duas referências fornecidas; nenhuma regeneração do personagem foi necessária.

## Cenários

Os fundos gerados com ImageGen são carregados automaticamente pelo nível em encontros comuns e principais:

- Nível 1: `assets/background_pedra_do_corte.png`, clareira tropical com pedras partidas e monólitos ancestrais.
- Nível 5: `assets/background_fortaleza_caida.png`, pátio de fortaleza em ruínas, árvores mortas e luz fria, para o bioma do Corpo Seco.

O cenário da Mata Sombria e o fundo exclusivo do tutorial continuam disponíveis. Os demais níveis mantêm o fundo padrão.

## Prompts usados no ImageGen

### Pedra do Corte

Production-ready 2D SIDE VIEW BATTLE BACKGROUND for a dark fantasy pixel-painted turn-based card game. Wide landscape 16:9, 1536x864 composition, no characters or creatures, no UI, no cards, no text. Biome: PEDRA DO CORTE, an ancient Brazilian tropical forest clearing with enormous split weathered standing stones, indigenous carved monoliths with subtle spiral carvings, mossy granite boulders, huge strangler fig roots and ferns, old stone steps disappearing into the dense forest at the center back. Atmospheric dawn fog, restrained jade green, teal shadows, muted warm gold light filtering through canopy. Keep the middle of the scene spacious and readable as a level earthen-and-stone combat arena. Character ground line around 58 percent from top, completely clear of foreground obstacles at x20 percent and x80 percent. Small stones, short moss and dusty worn flagstones on a continuous horizontal floor, no cliffs or water in the fighting area. Deep layered forest and ancient broken stone arch in distance. Detailed crisp pixel-painted art with rich organic texture, mature moody fantasy style, matching a hand-painted dark fantasy jungle RPG. Upper 15 percent low contrast for HUD and lower 27 percent quiet for card tray. Ground should remain continuous and clear. Full-bleed environment art only.

### Fortaleza Caída

Production-ready 2D SIDE VIEW BATTLE BACKGROUND for a dark fantasy pixel-painted turn-based card game. Wide landscape 16:9, 1536x864 composition, no characters, no enemies, no skeleton figures, no UI, no cards, no text. Biome: FORTALEZA CAÍDA, haunted ruins for a dry undead forest creature called Corpo Seco. A ruined ancient stone fortress courtyard reclaimed by dead twisted tree roots, collapsed ramparts and broken watchtowers in the background, dry leafless forest silhouettes, a few old carved grave markers on outer edges, weathered indigenous stone reliefs and vines around a sealed entrance. Ominous cold moonlight, smoky desaturated blue-green mist and faint muted amber braziers deep in the background; not a European gothic cathedral, grounded ancient South American stone fortress. Keep center scene clear as a horizontal combat arena with cracked stone flagstones, dry earth and sparse dead leaves. Character ground line around 58 percent from top; x20 and x80 percent must be unobstructed for small combatants. No foreground objects covering the arena. Deep atmospheric perspective, intricate crisp pixel-painted game art, antique dark fantasy mood. Upper 15 percent low contrast for HUD and lower 27 percent quiet for card tray. Full-bleed environment art only.


## Polimento visual do rugido e dos recortes

Guardião e Vinimuth passam por uma limpeza de matte no carregamento: só tons claros neutros conectados à transparência externa são removidos, até duas camadas de pixels. Assim o halo branco/cinza desaparece sem alterar a escala, os pivôs ou os detalhes claros internos. A limpeza também é aplicada aos retratos e projéteis usados pelo jogo.

O Rugido Espiritual agora tem três etapas visuais: preparação com selo no chão e partículas convergentes, voo com ecos e cauda de energia, e dissipação no alvo com ondas e fragmentos. Os efeitos seguem o relógio da animação e desaparecem quando o ataque termina. Dano, duração, frequência e regras do ataque permanecem iguais; as ultimates do jogador não foram alteradas.
