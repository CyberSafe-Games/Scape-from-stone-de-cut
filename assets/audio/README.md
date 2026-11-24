# Áudio do jogo

Coloque os efeitos sonoros e músicas nesta pasta. Os arquivos de áudio ainda não foram adicionados nesta etapa.

## Como registrar sons

No ponto de inicialização do jogo, registre os efeitos com identificadores estáveis:

```python
audio_manager.register_sounds({
    "ui.confirm": "ui/confirm.wav",
    "card.play": "cards/card_play.wav",
    "combat.hit": "combat/hit.wav",
})
```

Os caminhos acima são exemplos e só funcionarão depois que os respectivos arquivos forem adicionados. Para reproduzir um efeito, use `audio_manager.play_sfx("ui.confirm")`. As cenas podem acessar o serviço compartilhado por `scene_manager.audio_manager`.

Formatos recomendados para efeitos: WAV ou OGG. Para música de fundo, prefira OGG. Confira a licença de cada arquivo antes de incluí-lo no jogo.

## Trilha de despedida

- **Lost Time**, de Kevin MacLeod (Incompetech), ISRC `USUAN1500032`. [Página da faixa](https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1500032) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- O arquivo `music/epilogo_lost_time_v1.ogg` foi convertido do [MP3 do compositor](https://incompetech.com/music/royalty-free/mp3-royaltyfree/Lost%20Time.mp3) para Ogg Vorbis com fade de entrada de 650 ms. SHA-256 do original `c6c06198854392d729d965fc531cff8b3580c177944a1f7c8542b99edf3f7f65` e do OGG `f6e4d269cc2ed490e71448255d2b0317946ac0701fb2eef7535c3cdae6d11e96`.
