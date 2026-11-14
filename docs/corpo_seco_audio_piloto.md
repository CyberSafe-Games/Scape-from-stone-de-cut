# Corpo Seco — piloto de áudio

Quatro ações integradas usando somente o repertório existente.
Fontes, filtros e hashes em `corpo_seco_audio_fontes_v1.json`.
Originais, variantes anteriores e bosses aprovados preservados.

- Corte Rápido: movimento aos 24%, corte corporal e sangramento no contato aos 52%.
- Lâminas Cruzadas: duas passagens curtas a partir dos 24%; corte corporal aos 52%.
- Postura Defensiva: posicionamento de lâmina e aura discreta aos 52%, com cauda
  de aproximadamente 682 ms após a animação.
- Ataque Giratório: giro a partir do lançamento da Ultimate aos 40%; corte corporal
  no impacto aos 62%. O movimento termina suavemente antes do contato.

Os recortes de movimento cabem entre preparação e impacto. O contato reutiliza
o corte sincronizado da dupla, sem choque de metal contra o jogador.
As mecânicas, os danos e as animações não foram alterados.

Validação: RED confirmado antes das chamadas; 62 testes de áudio aprovados;
auditoria dos 65 efeitos sem excessos nos limites individuais; `git diff --check` aprovado.
Aprovação de timbre, peso e sincronização percebida pendente de escuta pelo jogador.

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py --corpo
```

1 corte; 2 cruzadas; 3 defesa; 4 giratório; Esc sai.
A prévia usa animações e fila de áudio reais, sem ler ou gravar saves.
