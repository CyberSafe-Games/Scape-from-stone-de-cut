# Zanzara — boss final

O confronto principal do Santuário de Pedra (nível 7) agora usa Zanzara.
Os encontros comuns da região continuam com Vinimuth e Mago do Santuário.
O retrato e o título da batalha identificam o novo boss final.

O desenho conserva rosto, cabelo, barba, sorriso e porte das duas referências.
A roupa é azul-marinho escuro, a faixa é branca e os bordados e acessórios
continuam dourados. Os personagens estão voltados para a esquerda, com
fundo transparente, paleta compartilhada e pés alinhados.

Sete sequências com oito frames (56 poses): repouso, dano, investida,
arremesso de moedas, onda de energia, amuleto e ultimate própria.
As moedas e a onda têm quatro desenhos independentes de projétil cada.
A ultimate tem quatro camadas próprias de carga, voo e impacto azul/dourado.

## Kit

190 de vida, 4 de energia e duas ações por turno completo.

| Ação | Efeito | Peso |
| --- | --- | --- |
| Investida Soberana | 15 de dano, corpo a corpo | 35% |
| Chuva de Moedas | 17 de dano, à distância | 25% |
| Onda Imperial | 20 de dano, à distância | 25% |
| Amuleto Dourado | Recupera até 16 de vida e renova +4 de dano por 2 turnos | 15% |
| Maré Soberana | 32 de dano, especial a cada 8 ações | Especial |

O amuleto não ataca e não acumula bônus de reaplicações. Durações seguem
os turnos completos do dono, preservando as regras existentes de combate.
Os projéteis surgem no lançamento e viajam até o jogador; flash, vida e
texto de dano aguardam o impacto. A ultimate dura 2900 ms, lança em 44%
e atinge em 80%. Ao derrotar Zanzara, a campanha segue a conclusão existente
do último território, sem adicionar outra fase ou alterar saves.

## Arquivos

- Sprites: `assets/bosses/eight_frames/zanzara`.
- Efeitos da ultimate: `assets/boss_ultimate_effects/zanzara`.
- Fontes preservadas: `assets/bosses/eight_frames/zanzara/source`.
- Geração pela ferramenta integrada de imagens; prompts: `docs/zanzara_prompts.json`.
- Exportação: `python -B devtools/prepare_zanzara.py`.
- Prévia sem saves: `python -B devtools/preview_zanzara.py`.
- Prévia animada: `docs/zanzara_em_acao.gif`.
