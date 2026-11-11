# Gordofera — piloto de áudio

Cinco ações integradas usando repertório existente. Sem novos downloads.
Fontes, créditos, receitas e hashes: `gordofera_audio_fontes_v1.json`.

- Garras Dilacerantes: movimento aos 24%, corte e sangramento no contato aos 52%.
  Reutiliza os sons aprovados do Guardião.
- Rugido Feroz: rugido de urso com timbre mais grave, iniciado aos 35%.
  A vocalização tem seu final preservado; sem eco acrescentado.
- Cabeçada Brutal: impacto corporal no contato aos 52%, mantendo o registro existente.
- Guarda Ferrenha: textura de pedra aos 52%, com cauda de cerca de 628 ms após a animação.
- Abalo Abissal: movimento do salto aos 25%; contato pesado e resquício de terra aos 64%,
  com cauda de cerca de 628 ms após a animação.

Mecânicas, dano e animações não alterados. Originais e outros bosses preservados.
Guardião, duas fases de Álvaro e Tex e Goblin Nerd foram aprovados pelo jogador;
a Gordofera ainda aguarda avaliação auditiva.

Validação: RED confirmado antes das chamadas; 60 testes direcionados aprovados;
auditoria dos 61 efeitos sem excessos nos limites individuais; `git diff --check` aprovado.
Esses resultados não substituem a escuta de timbre, peso e sincronização percebida.

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py --gordofera
```

1 garras; 2 rugido; 3 cabeçada; 4 guarda; 5 Abalo; Esc sai.
A prévia usa animações e fila de áudio reais, sem ler ou gravar saves.
