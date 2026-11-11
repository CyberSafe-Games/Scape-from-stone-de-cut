# Álvaro e Tex — áudio da primeira fase

Primeira versão para avaliação, derivada de recursos existentes no projeto.
Nenhum download novo foi feito. Receitas e hashes em
`alvaro_tex_audio_fase1_fontes.json`; reprodução da preparação em
`devtools/prepare_duo_audio.py` (não sobrescreve destinos).

- Estocada: movimento de lâmina aos 24% da animação; corte corporal no contato (58%).
- Estrela: lançamento/rotação aos 30%; corte corporal no contato do projétil (68%).
- Fumaça: ativação aos 52%; cauda por aproximadamente 636 ms após a animação.
- Vendaval: giro aos 24%; corte corporal no impacto (58%).

O som de movimento pode sugerir arma metálica; o impacto usa corte e sangramento
da adaga, sem adicionar estilhaços ou impacto de metal contra o jogador.
Os instantes e regras do combate foram preservados. A segunda fase não foi alterada.

Validação: RED confirmado antes das chamadas; 49 testes de áudio aprovados;
auditoria dos 44 efeitos sem excessos nos limites individuais adotados.
Qualidade percebida, timbre e encaixe continuam pendentes de aprovação do jogador.

Prévia sem saves, com animações e chamadas de som reais:

```powershell
.\.venv\Scripts\python.exe devtools/preview_guardian_audio.py --duo
```

1 estocada, 2 estrela, 3 fumaça, 4 Vendaval; Esc fecha.
O script conserva seu nome original e mantém o piloto do Guardião sem `--duo`.
