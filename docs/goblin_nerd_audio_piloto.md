# Goblin Nerd — piloto de áudio

Cinco ações integradas com sete OGG novos, preservando os originais externos.
Fontes, autores, licença indicada, filtros e hashes em `goblin_nerd_audio_fontes.json`.
Seleção baseada em metadados e análise de duração/envelope, sem alegar escuta crítica.

- Chave Arremessada: passagem curta no lançamento (30%); contato corporal (74%),
  reutilizando o impacto do porrete do Pequeno, sem choque de metal contra o jogador.
- Descarga Improvisada: plasma + zap elétrico no lançamento (30%); impacto de energia (58%).
- Baforada Tóxica: sopro orgânico + gás + borbulhamento discreto, aos 35% da ação.
- Escudo Rúnico: ativação tecnológica + detalhe rúnico aos 52%; cauda de cerca de 820 ms após a animação.
- Descarga Sobrecarregada: carga aos 10%, feixe no lançamento (44%) e impacto (77%).

Os recortes removem antecipações excessivas; o impacto energético tem o ataque
do arquivo alinhado ao início. Ganhos deixam margem de pico/RMS sem sobrescrever fontes.
Os instantes vêm da animação real; dano e regras de combate não foram alterados.
Guardião e as duas fases de Álvaro e Tex aprovados pelo jogador permanecem preservados.

Validação: RED confirmado antes das chamadas; 54 testes direcionados aprovados;
auditoria de 56 efeitos sem excessos nos limites individuais; `git diff --check` aprovado.
Avaliação de timbre, força e sincronização percebida pendente no piloto.

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py --goblin
```

1 chave; 2 descarga; 3 baforada; 4 escudo; 5 Ultimate; Esc sai.
A prévia usa as animações e a fila de áudio reais, sem ler nem gravar saves.
