# Carrasco da Vigília — piloto de áudio

Quatro ações integradas com repertório existente, sem novos downloads.
Fontes, filtros e hashes em `carrasco_audio_fontes_v1.json`.
Os bosses aprovados, as mecânicas e as animações foram preservados.

- Corte do Carrasco: passagem de machado aos 24%, impacto corporal e sangramento aos 52%.
- Varredura Escarlate: movimento mais encorpado aos 24%, contato corporal aos 52%.
- Vigor Escarlate: aura aos 52%, com cauda de cerca de 780 ms após a animação.
- Execução Escarlate: movimento aos 40% da Ultimate, impacto mais pesado aos 64%
  e sangramento na continuação. Sem choque metálico contra o jogador.

Validação: RED confirmado antes da integração; 64 testes direcionados aprovados;
auditoria dos 70 efeitos sem excessos nos limites individuais; `git diff --check` aprovado.
Avaliação auditiva de timbre, peso e encaixe pendente pelo jogador.

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py --carrasco
```

1 corte; 2 varredura; 3 vigor; 4 execução; Esc sai.
A prévia usa animações e chamadas reais de áudio sem ler ou gravar saves.
