# Etapa final — trilha sonora

Branch: feature/trilha-sonora. Direção aprovada: fantasia sombria com percussão e elementos da floresta. As 75 cartas novas estão fora do escopo.

## Seleção aprovada e integrada

| Contexto | Faixa | Tecla no piloto |
| --- | --- | --- |
| Menu, seleção de save, mapa, mochila e loja | Deep forest — PoshPony | 1 |
| Combates comuns e tutorial | The Last Stand — CharlVera | 2 |
| Chefes, inclusive as duas fases de Álvaro e Tex | Jungle Chase — VasilYatsevich | 6 |
| Zanzara, boss final | Jungle Tribe — VasilYatsevich | 3 |

A seleção acima foi aprovada pelo usuário no piloto. Jungle Guerilla, Ritual Horror e Ritual of the Ancients ficam preservadas como candidatas antigas e não entram na seleção ativa.

## Integração

- Configuração: src/config/music.py. Volume inicial 45%, igual ao piloto aprovado.
- SceneManager acompanha o contexto musical da cena e usa MusicDirector, sem reiniciar uma faixa que continua adequada ao contexto.
- Transição não bloqueante: saída de 350 ms e entrada de 600 ms, usando apenas o canal de música. Efeitos sonoros permanecem independentes.
- Menu e mapa compartilham a mesma faixa; modais e troca de fase de Álvaro e Tex não reiniciam a música.
- Vitória, derrota e encerramento do confronto retiram a trilha gradualmente, preservando os efeitos de vitória/Game Over existentes. Ao voltar ao mapa ou reiniciar um combate, a trilha correspondente retorna.
- A seleção usa o inimigo real, não apenas o número do território. Encontros comuns na última região não recebem antecipadamente a trilha de Zanzara.
- As faixas repetem pelo mixer. Continuidade musical da repetição e volume perceptual devem ser conferidos no teste final pelo usuário; não houve escuta crítica pelo assistente.

## Recursos

Originais e fontes: pasta externa outputs/trilha-sonora. Todos os MP3 usados foram conferidos por SHA-256 antes/depois do preparo. Os arquivos das faixas 1 e 2 permaneceram idênticos durante a rodada 2.

OGG ativos: menu_floresta_v1, combate_tambores_v1, chefes_jungle_chase_v2 e chefes_jungle_tribe_v2, em assets/audio/music. Fontes, licenças, avisos de Content ID/IA e filtros: docs/trilha_sonora_fontes_v1.json e docs/trilha_sonora_fontes_v2.json. Nenhuma gravação, sample ou melodia da referência de Tarzan foi usada.

## Avaliação

Abrir testar_trilha_sonora.bat. O piloto usa o mesmo seletor musical da campanha e cenas reais, com um save temporário só para desenhar o mapa; não encaminha cliques para a campanha nem lê/escreve os saves reais.

- 1, 2, 3 e 6: escolher o contexto aprovado.
- A/S/D/F: executar golpes junto da música.
- Cima/Baixo: ajustar o volume; M: silenciar a música; espaço: reiniciar a faixa.
- T: alternar menu/mapa na faixa 1; Esc: sair.

## Validação

- 102 testes dos efeitos e sistema de áudio aprovados.
- 6 testes novos aprovados: roteamento dos chefes e Zanzara, encontros comuns na região final, saída em vitória/derrota, continuidade entre menu/mapa e fases, troca gradual com pedidos rápidos e uso do fade do mixer.
- Piloto --smoke aprovado sem janelas: quatro músicas carregadas e reproduzindo no contexto esperado, menu/mapa renderizados e golpes acionados.
- git diff --check aprovado.

Próximo fechamento: conferência do jogo completo no main.py e preparação da PR própria da trilha após aprovação do usuário. Não adicionar esta etapa à PR #13 nem fazer merge na main sem aprovação do grupo.
