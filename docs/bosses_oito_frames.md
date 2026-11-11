# Bosses — oito quadros, cores e fluidez

## Versão atual

Os cinco bosses possuem kits completos de oito quadros. Álvaro e Tex contam
com duas formas. As quatro sequências antigas foram substituídas por folhas
completas coerentes: não há mais alternância entre poses antigas escuras e
desenhos novos claros. A referência de cor é a arte nova aprovada pelo usuário.

São 41 grupos ativos, com 328 sprites individuais. Ataques, defesa, cura/buff,
reação de dano, idle, ultimates e transição usam as mesmas cores do personagem.
As habilidades e a transição de Álvaro e Tex que já tinham oito quadros foram
harmonizadas por material e por sequência, preservando sua animação original.

## Correções

- Uma paleta fixa por boss, sem ajustes de brilho diferentes a cada quadro.
- Corpo opaco, removendo fantasmas na reação de dano e preservando a
  transparência dos efeitos mágicos e da fumaça.
- Recorte nos intervalos reais entre linhas da folha, evitando cortar pés
  quando a grade gerada não tem espaçamento perfeitamente uniforme.
- Escala calculada a partir da postura inicial, sem encolher o corpo quando
  a arma é levantada ou o efeito cresce.
- Correção da ordem do combo pesado do Carrasco: giro antes do golpe no chão.
- Ataque de arremesso do Goblin com chave de fenda e recuperação da mão vazia;
  a pistola pequena permanece no disparo e na ultimate.
- Último quadro das habilidades e do dano fecha na mesma postura do idle.
- A transição da dupla fecha exatamente no idle da segunda fase.
- O relógio de idle reinicia após ataques, suporte, dano e transição. Antes,
  o relógio global podia devolver o personagem a um quadro aleatório.
- Impactos e lançamentos respeitam as poses correspondentes. Nos especiais
  corpo a corpo, a pose de impacto coincide com o instante real do golpe.
- Nos golpes comuns dos bosses, a barra de vida e o texto de dano também
  aguardam o impacto. A tela de derrota espera o término de um golpe fatal.

Os valores de vida, dano, energia, cura e buffs permanecem iguais. Os efeitos
mágicos aprovados continuam sendo desenhados por camadas. O protagonista e os
inimigos comuns não fazem parte desta etapa de padronização dos bosses.

## Arquivos e reprodução

Sprites finais: `assets/bosses/eight_frames/<boss>/<grupo>_1.png` até `_8.png`.
`manifest.json` lista os grupos; cada pasta contém sua `palette.json`.

| Referência de oito quadros | Arquivo gerado com a ferramenta integrada |
| --- | --- |
| Guardião | `assets/bosses/eight_frames/guardiao_da_pedra/sequence_v2.png` |
| Goblin Nerd | `assets/bosses/eight_frames/goblin_nerd/sequence_v2.png` |
| Corpo Seco | `assets/bosses/eight_frames/corpo_seco/sequence_v2.png` |
| Carrasco | `assets/bosses/eight_frames/carrasco_da_vigilia/sequence_v2.png` |
| Álvaro e Tex, idle e dano das duas formas | `assets/bosses/eight_frames/alvaro_tex_sequence_v2.png` |

Prompts completos desta revisão: `boss_palettes_sequences_prompts.json`.
As referências e prompts da primeira expansão permanecem no projeto como histórico,
mas não são mais intercalados pelo preparador atual.

```bash
python devtools/polish_boss_sequences.py
python devtools/preview_boss_eight_frames.py
python -m pytest -q
```

`prepare_boss_eight_frames.py` também reconhece as novas folhas e encaminha para
o preparador atual, impedindo que uma nova exportação restaure a antiga mistura.
Esses comandos usam arquivos locais; não fazem novas chamadas à geração de imagens.

Testes cobrem contagem e uso dos quadros, paleta comum, estabilidade de brilho,
transparência, pivô, fechamento no idle e reinício do relógio após as habilidades.
Prévia atualizada: `bosses_cores_fluidas.gif`.
