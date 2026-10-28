# Mapa e encontros individuais

A campanha mantém os sete territórios e os três encontros anteriores a cada confronto principal. Agora são 21 círculos selecionáveis e sete losangos. O primeiro encontro começa liberado; cada vitória abre apenas o ponto seguinte. O losango só é liberado após os três encontros. Vencer o losango abre o próximo território.

## Voltar e repetir

Pontos verdes podem ser repetidos, inclusive encontros comuns de territórios já concluídos. A repetição concede as recompensas normais da luta, mas não aumenta a contagem de encontros, não pula etapas e não reduz o checkpoint da campanha. Sair durante uma batalha continua voltando ao mapa, sem registrar vitória.

O registro existente `encontros_por_territorio` continua sendo usado. Saves antigos não precisam reiniciar; a contagem anterior identifica quais círculos já estão concluídos. O índice do encontro escolhido é passado ao combate e à gravação da vitória. Dados são restaurados caso a gravação falhe.

## Controles

- Clique num círculo ou losango para inspecionar o ponto e use o botão da lateral para jogar.
- Setas percorrem todos os 28 pontos; Enter ou Espaço iniciam o ponto selecionado quando liberado.
- Teclas 1–7 selecionam o próximo encontro disponível de cada território.
- Loja, mochila e retorno ao menu mantêm os controles existentes.

## Arte

Arquivo: `assets/ui/world_map.png`. Criado com ImageGen, em 1536 × 1024, sem textos ou marcadores fixos. Caminhos, estados e seleção são desenhados pelo jogo sobre a arte.

Direção usada na geração: mapa de mundo em pixel art pintada de fantasia sombria, visto de cima, com floresta tropical brasileira, templos indígenas em pedra, rios, pântano luminoso, fortaleza caída, montanhas azul-acinzentadas e santuário dourado. Paleta de jade, verde-azulado, bronze e ocre. Composição em zigue-zague da clareira inferior esquerda ao santuário superior direito, com espaço para os controles interativos. Sem personagens, cartas, interface, letras ou números na imagem.
