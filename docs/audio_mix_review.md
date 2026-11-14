# Revisão inicial da mixagem

Base: `origin/main` em `b69cdd9`; branch local `feature/audio-enemies`.
Atualização por fast-forward, sem commit novo ou publicação. Alterações locais
de inimigos preservadas por combinação em três vias.

## Calibração técnica

Os 34 efeitos registrados em `main.py` têm ganhos explícitos em
`src/config/audio_mix.py`. Nenhum arquivo OGG foi sobrescrito.
Os ganhos são multiplicados pelos volumes geral, de efeitos e da chamada.
Não há chamada de música de fundo no código atual.

Referências iniciais de calibração, escolhidas para deixar margem de mistura:
pico de amostra até -9 dBFS e RMS dos blocos ativos até -22 dBFS.
Esses valores não são um padrão de loudness nem substituem a escuta.
O relatório `audio_mix_audit.json` contém as medidas antes e depois, considerando
a quantização do volume do Pygame. As chamadas podem atenuar ainda mais o efeito.

Para reproduzir a auditoria na raiz:

```powershell
.\.venv\Scripts\python.exe devtools/audit_audio_mix.py
```

Resultado: 34 efeitos carregados; nenhum acima das referências após o ganho.
O soco, impacto da investida e machados gêmeos exigiram as maiores atenuações.
Há amostras no limite digital em alguns originais; reduzir ganho não reconstrói
picos já cortados. Não foi avaliado true peak, LUFS ou a soma de canais simultâneos.

## Testes

- Novo teste de cobertura dos ganhos: RED antes da configuração, GREEN depois.
- Áudio (mixagem, gerenciador, gameplay, inimigos e interface): 79 testes aprovados.
- Atualização (áudio, janelas e animações de 12 quadros): 103 de 105 aprovados;
  dois erros por `numpy` ausente nos testes visuais de paleta do protagonista e bosses.
  Nenhuma conclusão de aprovação foi atribuída a esses dois testes.
- `git diff --check`: aprovado.

## Conferência manual pendente

Ouvir em volume confortável, com o mesmo volume de sistema durante a comparação:

- Menu, navegação, confirmação, cartas e atalhos F10/F11.
- Soco, investida e machados: verificar se ainda há som áspero ou distorcido.
- Projéteis: conferir lançamento, contato e sincronização com as 12 poses.
- Escudos, poções, poderes, Ultimate, vitória e derrota.
- Ações de inimigos já mapeadas e sons sobrepostos ao clique ou aos impactos.

Registrar quais efeitos ficaram fortes, fracos ou ainda distorcidos.
Se a aspereza persistir mesmo com o volume reduzido, revisar o recurso de origem
ou produzir uma nova variante em outro arquivo, preservando o atual.
Novos sons de inimigos ficam para depois dessa escuta.
