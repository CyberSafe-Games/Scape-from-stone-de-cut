# Implementação roguelite para avaliação

> **Registro histórico — não é especificação vigente.** Valores, caminhos, comandos e resultados abaixo pertencem à etapa original. Não restaurar regras/arte antigas nem executar preparadores sobre kits atuais. Consulte o [estado atual](estado_atual.md).

> Estado para o playtest de 18/11: [roteiro do grupo](playtest_balanceamento_grupo.md), [cura progressiva](validacao_cura_progressiva.md) e [especiais custando 5](validacao_especiais_custo5.md). O usuário autorizou publicar a branch e abrir PR, sem merge. As contagens e regras anteriores abaixo registram etapas históricas.

17/11/2026, branch `feature/balanceamento-roguelite`, base `ad593a5`. Implementação autorizada pelo usuário após a entrega do diagnóstico. Sem commit, push ou merge. Arte, sprites, retratos, músicas e arquivos de efeitos aprovados foram preservados; não há dependências novas.

## Comportamento disponível

**Regra da cura naquela etapa:** até três compras por run, recuperando até 20 de vida atual cada, por 30/45/60 ouro. Contador e preço persistem no save v14; cheia não cobra/consome, quarta compra esgota. Nova run zera contador. Saves v13 iniciam esse contador em zero, sem inventar compras anteriores, preservando HP, ouro e perfil; original guardado em `.v13.bak`. As descrições e simulações de cura ilimitada abaixo são históricas.

Revisão posterior aprovada pelo usuário: a oferta de vida máxima temporária foi substituída por **cura de até 20 de vida atual por 30 ouro**, limitada à vida máxima, sem cobrar quando cheia. Aumento de vida máxima fica nas melhorias permanentes por fragmentos; morrer não concede atributo automaticamente. Compras temporárias feitas antes da mudança continuam válidas somente até o fim daquela run, preservando o investimento anterior. O contador legado não recebe novas compras e zera na nova run. Não foi necessário mudar o formato v13 do save.

Validação dessa revisão: **53 testes direcionados aprovados** (`test_shop_and_combat_reset`, `test_roguelite`, `test_life_recovery_after_combat`, `test_save_system`), incluindo cura parcial, vida cheia, saldo insuficiente, rollback, isolamento de slots, bloqueio em combate/morte e bônus legados. Prévia sem janela aprovada com clique na cura e asserções de HP/saldo; painel inspecionado visualmente. Suíte completa não repetida para essa alteração localizada; o relatório de 636 testes abaixo registra a consolidação anterior.

- Perfil por slot, com fragmentos, vida/energia permanentes e preparação de cartas. JSON v13 separa `perfil` de `run`; `progresso` existe como projeção compatível em memória. Migrar preserva o original em `.json.v12.bak`, sem fragmentos retroativos. Revisão de arquivo rejeita documento desatualizado; não há restauração automática de backups mortos.
- Morte encerra a run. R ou o botão abrem preparação; nova run limpa mapa, ouro, aquisições, materiais, N2 e melhorias temporárias, preservando perfil e flags do tutorial. Inicia com vida cheia e 30 ouro; na primeira jornada, o tutorial concede esses mesmos 30 uma única vez.
- Run viva pode ser retomada com HP, Escudo, efeitos, mão/pilhas, energia, Ultimate, plano de intenções e fase do chefe. O mapa oferece Retomar combate salvo e bloqueia loja/Mochila enquanto houver encontro em andamento. Resultado e seleção pendente são persistidos; recuperação de queda garante somente a última gravação concluída. Manipulação manual de backups não é impedida.
- Cada tipo desbloqueado cria três instâncias N1 identificadas. Os 18 espaços guardam referências individuais; reserva de material é separada. N1 e N2 contam juntos no máximo de três cópias por tipo. Desequipar não produz cópias, materiais ou nova oportunidade de upgrade.
- Loja → Materiais / Evoluir cópias: material custa 15 ouro, até nove por tipo. Evolução escolhe uma instância N1 e consome exatamente três materiais desse tipo + o preço individual do diagnóstico. Até três evoluções por run, mesmo desequipadas. Falha de gravação restaura os saldos e o inventário.
- Primeira vitória: até dois tipos novos ou material direcionado (um no comum/três no chefe), ou pular. Revanches são treino: preservam estado persistente da run e não concedem ouro, cartas, materiais, cura ou fragmentos. A fase de Tekks permanece o mesmo encontro.
- Ouro fixo e fragmentos seguem a tabela do diagnóstico. Crédito do ouro é lógico; partículas são só apresentação. Fragmentos de chefe são persistidos antes de escolher carta/material, sem duplicar em nova confirmação. Vitória final encerra a run com resumo/preparação.
- N1, N2, preços e valores de chefes seguem a proposta registrada. Os textos das cartas e intenções são compostos na renderização sobre os PNGs originais; não há regeneração de arte. N2 possui badge e descrição própria. Limites globais de Veneno, Sangramento, Choque e Ultimates foram preservados.

## Validação técnica

- **636 testes aprovados em 66 módulos**, consolidados por processos isolados. O relatório foi retomado após correções, preservando aprovações anteriores; módulos afetados por ajustes posteriores foram repetidos de forma dirigida. O tempo final de `36,3 s` no JSON corresponde à última retomada, não ao tempo total de todas as tentativas.
- [Relatório por módulo](validacao_balanceamento_por_modulo.json). Foram criados 18 testes específicos de evolução, reset, isolamento, transações, duplicação de prêmios, migração e snapshots. Expectativas numéricas anteriores foram atualizadas apenas nas regras que mudaram.
- O módulo de tutorial compartilha AssetManager no mesmo processo de testes, evitando recarregar centenas de MB em cada caso. Isso eliminou o timeout, sem retirar testes.
- `devtools/preview_roguelite.py --smoke`: loja, oficina, Mochila, batalha, recompensa, seletor de materiais e preparação renderizados com saves temporários. Compra de material e escolha de recompensa também acionadas por mouse mapeado em 1280×720. Imagens em `tools/roguelite-qa/` (ignoradas pelo Git), inspecionadas para corrigir sobreposições. Não houve avaliação perceptual de áudio ou animação.
- Após ajustes visuais finais, mais 35 verificações dos módulos de coleção/mapa/rascunho passaram. `git diff --check` sem erros.

## Simulação e limites de balanceamento

Atualização: a amostra de 15 campanhas abaixo é histórica, da primeira política do bot. A avaliação atual cobre **60 campanhas com o bot corrigido**, cura, composição de deck, evolução de cópias equipadas e comparação de Ultimates. Ver [fechamento técnico e roteiro](fechamento_balanceamento_roguelite.md). A consolidação incremental de testes atual passou a **643 testes em 67 módulos**.

[Resultados de 15 campanhas heurísticas](simulacao_balanceamento_roguelite.json): cinco sementes por estratégia, compras e recompensas reais, sem melhorias permanentes, sem N2 e sem compras temporárias de vida. Todas usam Forças Ancestrais; não representam todas as preparações possíveis.

| Política | Campanhas completas | Observação |
|---|---:|---|
| Dano + Aura | 0/5 | Parou entre o sexto e o 12º encontro |
| Defesa + cura | 2/5 | Sementes 0 e 3 completaram; duas outras chegaram a Zanzara e perderam |
| Veneno + Sangramento | 0/5 | Parou entre o sexto e o 13º encontro |

Isso demonstra duas rotas reproduzíveis de vitória sem atributos permanentes, mas **não demonstra equilíbrio entre estratégias**. A política de compras, deck e combate é simples: não usa toda a loja, todas as Ultimates, N2 ou materiais direcionados. Falha de bot não prova impossibilidade humana; sucesso de defesa/cura também não descarta abuso de sustentação. O montador foi corrigido para não criar um deck de cura sem ataques antes de obter Arco. Resultados anteriores à correção foram substituídos.

Próxima avaliação humana: conferir abertura da run, primeira evolução, diferença de moedas, encerramento na morte, retomada e chefes finais. Especial atenção à vantagem de cura em deck curto e à pressão de Jozephino sobre estratégias ofensivas. Não houve campanha completa jogada por uma pessoa nesta sessão, nem escuta crítica de sincronismo. Não publicar como balanceamento final já validado.

## Como testar

No PowerShell do projeto:

```powershell
.\.venv\Scripts\python.exe main.py
# Somente dados temporários e sem janela:
.\.venv\Scripts\python.exe -B devtools/preview_roguelite.py --smoke
# Executa uma amostra atual com preparação, cura e LV2:
.\.venv\Scripts\python.exe -B devtools/simulate_roguelite_balance.py --seeds 5 --upgrades
```

No jogo, abra Mochila para conferir N1/N2 e reserva; na loja abra Materiais / Evoluir cópias. Após morrer, compre melhorias com fragmentos e inicie outra run. Ao sair de um combate vivo, use Retomar combate salvo no mapa. O Laboratório permanece isolado e invulnerável. A avaliação final usa uma única instância do `main.py`, não vários pilotos de personagens.
