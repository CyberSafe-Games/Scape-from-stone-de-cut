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
| Zanzara | music/chefes_jungle_tribe_v2.ogg |

Configuração: src/config/music.py. Volume inicial 45%, saída 350 ms e entrada
600 ms; a fase da dupla não reinicia a faixa. Novos derivados em OGG com
origem/licença/composição registradas; preservar originais e recursos aprovados.
Não registrar IDs/arquivos exemplificativos inexistentes. Fallback tolerado
pelo runtime não substitui teste de presença do asset.

Validação: testes de áudio, mix, opções, UI e MusicDirector. Confirmação da
Mochila é atenuada a 65%. Ver [estado atual](../../docs/estado_atual.md).
