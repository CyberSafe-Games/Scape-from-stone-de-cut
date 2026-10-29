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
