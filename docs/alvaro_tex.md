# Álvaro e Tex — Mata Sombria

O ponto principal do segundo bioma agora enfrenta Álvaro e Tex. Os três encontros
comuns continuam usando Macaco Selvagem e Guerreiro da Mata.

## Duas fases, uma luta

1. **Dupla: 76 de vida.** Estocada (9), shuriken (7), Fumaça Restauradora
   (recupera até 10 de vida e concede +3 de dano por dois turnos completos,
   sem acumular ao reaplicar). A fumaça permanece na dupla, sem causar dano
   ou veneno no jogador. Especial: Vendaval da Dupla (15).
2. **Pequeno sozinho: 44 de vida.** Chute (7), porrete (9), shuriken (6).
   Especial: Fúria do Pequeno (13), com golpe no chão, poeira e rastros.

Ambas fazem duas ações por rodada. O especial acontece a cada oito ações e fica
indicado na intenção, como nos demais chefes. A segunda fase inicia seu próprio
contador. A barra identifica a fase atual (1/2 ou 2/2).

Ao zerar a primeira barra, a carta/ultimate termina antes da sequência de fumaça
e queda, de oito quadros e dois segundos. Cartas ficam visíveis, mas ações são
bloqueadas durante essa transição. O pequeno entra com a própria barra cheia.
Não há moedas, recompensa ou conclusão do território antes da segunda derrota.

Vida, escudo, força, efeitos, energia, mão, pilhas, uso da troca do cemitério e
carga da ultimate do jogador permanecem. A carta final é descartada e paga
normalmente. Os efeitos do parceiro derrotado não passam ao pequeno. Se fogo,
veneno ou sangramento derrubarem a dupla na rodada inimiga, suas ações restantes
são canceladas e uma rodada normal do jogador começa após a transição.

O formato dos saves não muda. Como as demais batalhas, sair e carregar novamente
reinicia o confronto territorial na primeira fase; não salva uma luta pela metade.

## Arte e reprodução

Fontes do ZIP `alvaro e tex.zip` preservadas em
`assets/bosses/alvaro_tex/source/`. Preparação:

```bash
python devtools/prepare_alvaro_tex.py
python devtools/preview_alvaro_tex.py
```

Cada fase conserva **oito poses distintas por habilidade**, quatro de idle e quatro
de dano. A primeira tem também oito poses para a transição. O jogo escolhe os
quadros pelo tempo decorrido, sem limitar essas sequências aos quatro quadros dos
chefes antigos. Idle percorre as poses de ida e volta para suavizar a respiração.

Os sprites foram espelhados para a esquerda, separados com transparência e
alinhados pelos pés. Removidos os alvos cinzentos ilustrativos e os projéteis
destacados das poses de arremesso. A estrela foi recortada do desenho extra da
própria folha e gira separadamente até o jogador. Sinais de cura ao redor da dupla,
rastros, estilhaços e brilho dos especiais são complementos desenhados pelo jogo. Os personagens não
foram redesenhados. O cenário existente da Mata Sombria continua aplicado.

Prévia: `alvaro_tex_em_acao.gif`; folhas: `alvaro_tex_sprites.png`.
