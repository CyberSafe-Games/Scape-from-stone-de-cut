# Guardião da Pedra — piloto de seleção autônoma

Quatro ações integradas na branch `feature/audio-enemies`. Origens, autores,
licença informada e hashes estão em `guardiao_audio_fontes.json`.
Os MP3 externos foram somente lidos. Nenhum OGG existente foi sobrescrito.

| Ação | Fonte Pixabay | Tratamento e disparo |
|---|---|---|
| Golpe de Garras | Scorpion Claw Attack (4), Yodguard | Corte e aceleração preservando o pitch; 450 ms no contato |
| Pele Rochosa | Earth Spell, DRAGON-STUDIO | Remove silêncio inicial, acelera; 600 ms na ativação |
| Vigor Selvagem | Fantasy Healing Spell Soft Magic Chime #1, Vadim_Makes_Sound | Corte, aceleração e volume discreto; 700 ms na ativação |
| Rugido Espiritual | Colossal Dragon Roar, DRAGON-STUDIO | Trecho principal a partir de 2,8 s, eco curto; 1500 ms no lançamento |

Todos receberam filtros de graves/agudos e fades curtos. O ganho de preparação
deixa margem de pico/RMS; o volume de reprodução continua ajustável em
`src/config/audio_mix.py`. A primeira variante do rugido ficou fraca na medição;
foi preservada, e o jogo usa a variante `_v2` com o trecho principal.

## Validação técnica

- RED: nenhuma das quatro ações reproduzia som antes da integração.
- GREEN: 45 testes direcionados passaram.
- Cancelamento, quadro muito longo, disparo único e instante de disparo cobertos.
- Quatro ações percorridas e renderizadas com drivers dummy na prévia.
- Auditoria final: 38 efeitos carregados, nenhum acima dos limites individuais.
- Após a troca do rugido por v2: 10 testes de inimigos/mixagem passaram novamente.
- `git diff --check` aprovado.

## Avaliação pelo jogador

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py
```

Teclas: **1** garras; **2** defesa; **3** cura; **4** Ultimate; **Esc** sair.
A prévia usa animações, fila e mixagem reais, com ações disparadas manualmente.
Não lê nem grava saves e não simula dano/cura das ações.
Os quatro sons também estão ligados ao combate normal.

Pendente: escuta crítica pelo jogador para aprovar timbre, volume, duração,
encaixe no personagem e rugido espiritual. Seleção original baseada em metadados;
as verificações técnicas não equivalem a aprovação auditiva.
Sem commits, publicação ou mudanças nas mecânicas de combate.
