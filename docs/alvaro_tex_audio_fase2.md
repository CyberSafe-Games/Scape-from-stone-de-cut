# Álvaro e Tex — Pequeno, fase 2

Piloto derivado do repertório existente, sem novos downloads.
Primeira fase e Guardião aprovados pelo jogador; segunda fase ainda aguarda escuta.

- Chute Ardiloso: conserva o impacto corporal já integrado no contato.
- Pancada de Porrete: movimento abafado aos 24% e impacto corporal aos 60%.
- Shuriken Furtiva: reutiliza o giro aprovado na primeira fase; lançamento aos 38%
  e corte corporal no contato do projétil aos 72%.
- Fúria do Pequeno: movimento rápido aos 24% e sequência curta de impactos
  corporais a partir do contato aos 60%, sem sangramento de lâmina.

Composições, filtros e hashes: `alvaro_tex_fase2_audio_fontes.json`.
Os recursos anteriores não foram sobrescritos. Mecânicas e animações preservadas.
O mapeamento combina as ações novas com o chute básico já existente.

Validação: RED confirmado; 51 testes de áudio aprovados; auditoria dos 49 efeitos
sem excessos nos limites individuais adotados; `git diff --check` aprovado.
A qualidade percebida depende da conferência no piloto.

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py --small
```

Teclas: 1 chute; 2 porrete; 3 shuriken; 4 Fúria; Esc sair.
A prévia não lê nem grava saves. `--duo` continua abrindo a primeira fase.
