# Áudio do jogo

> Referência vigente — auditoria de 23/11/2026. [Estado atual](../../docs/estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Efeitos e trilha já estão integrados. IDs estáveis registrados em main.py pelo
AudioManager; acesso via scene_manager.audio_manager. Ganho por som/categoria
em src/config/audio_mix.py; preferências separam música, efeitos, interface e dano.

| Contexto | Arquivo relativo a assets/audio |
|---|---|
| Menu/mapa/Mochila/Loja/Altar | music/menu_floresta_v1.ogg |
| Combates comuns/tutorial | music/combate_tambores_v1.ogg |
| Chefes | music/chefes_jungle_chase_v2.ogg |
| Zanzara / início do epílogo | music/chefes_jungle_tribe_v2.ogg |
| Despedida no epílogo | music/epilogo_lost_time_v1.ogg |

Configuração: src/config/music.py. Volume inicial 45%, saída 350 ms e entrada
600 ms; a fase da dupla não reinicia a faixa. Novos derivados em OGG com
origem/licença/composição registradas; preservar originais e recursos aprovados.
Não registrar IDs/arquivos exemplificativos inexistentes. Fallback tolerado
pelo runtime não substitui teste de presença do asset.

Validação: testes de áudio, mix, opções, UI e MusicDirector. Confirmação da
Mochila é atenuada a 65%. Ver [estado atual](../../docs/estado_atual.md).



## Trilha de despedida

- **Lost Time**, de Kevin MacLeod (Incompetech), ISRC `USUAN1500032`. [Página da faixa](https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1500032) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- O arquivo `music/epilogo_lost_time_v1.ogg` foi convertido do [MP3 do compositor](https://incompetech.com/music/royalty-free/mp3-royaltyfree/Lost%20Time.mp3) para Ogg Vorbis com fade de entrada de 650 ms. SHA-256 do original `c6c06198854392d729d965fc531cff8b3580c177944a1f7c8542b99edf3f7f65` e do OGG `f6e4d269cc2ed490e71448255d2b0317946ac0701fb2eef7535c3cdae6d11e96`.
