# Playtest do balanceamento roguelite

> **Registro histórico — não é especificação vigente.** Valores, caminhos, comandos e resultados abaixo pertencem à etapa original. Não restaurar regras/arte antigas nem executar preparadores sobre kits atuais. Consulte o [estado atual](estado_atual.md).

> Para a revisão posterior de cartas, usar `feature/refino-cartas-roguelite` e o roteiro [playtest_refino_cartas.md](playtest_refino_cartas.md). A PR #24 já foi integrada; as observações abaixo descrevem o primeiro playtest.

Esta branch é uma versão experimental para avaliação do grupo. O objetivo é observar dificuldade e variedade de estratégias antes de integrar na main.

## Baixar e executar

Com o jogo fechado e sem alterações locais pendentes, no PowerShell da pasta do projeto:

```powershell
git fetch origin
git switch --track origin/feature/balanceamento-roguelite
# Se a branch já existir localmente: git switch feature/balanceamento-roguelite
# Depois, atualizar com: git pull --ff-only
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Se a venv já estiver pronta, basta instalar as dependências e executar. Não é necessário instalar dependências de desenvolvimento para jogar. A PR não contém executável empacotado.

## Primeira tentativa comparável

Use um **slot comum novo**, sem apagar seus saves anteriores e sem entrar no Laboratório invulnerável. Inicie sem melhorias permanentes. Pode usar loja, cura, recompensas, qualquer especial e evoluir até três cópias. Depois da primeira morte, registre o resultado antes de iniciar outra run; tentativas posteriores com melhorias devem ser anotadas separadamente.

Se todos os slots estiverem ocupados, preserve uma cópia da pasta `saves/` fora do projeto antes de usar outro conjunto de saves. A migração cria backups, mas não deve substituir essa cópia: versões anteriores do jogo não devem abrir o mesmo save já migrado para v14.

## O que mudou

- Morte encerra a run; nova run preserva o perfil, fragmentos e melhorias permanentes.
- Cartas têm cópias individuais LV1/LV2. Evoluir custa três materiais do tipo mais ouro; limite de três evoluções por run.
- A loja oferece três curas de até 20 HP por run: 30, 45 e 60 ouro. Vida máxima permanente usa fragmentos entre runs.
- Os três especiais precisam de 20 de carga e custam 5 de energia ao ativar. Sem energia suficiente, continuam prontos para os próximos turnos. Mana Ancestral paga antes de restaurar a energia para 8.
- Combate vivo pode ser retomado; cartas, efeitos, energia, inimigo e fase são preservados.
- Ouro, cartas e ações de chefes receberam ajustes de balanceamento. Revanches não dão recursos extras.

A arte dedicada do fragmento ainda depende da equipe; a concessão lógica já está implementada. As 75 cartas em desenvolvimento continuam bloqueadas.

## Registro de cada tentativa

Copie e preencha após morrer ou concluir:

```text
Jogador:
Tentativa nº / experiência prévia com o jogo:
Perfil novo? Melhorias permanentes existentes:
Especial escolhido:
Deck principal e cópias LV2:
Curas da loja usadas (0–3):
Último território e inimigo / campanha concluída:
Vida ao terminar cada território, se anotada:
Tempo aproximado da run:
O que mais causou dificuldade:
Alguma estratégia ou carta pareceu forte demais?
Alguma regra ficou confusa? Bugs observados:
```

Para uma medição sem ajuda, evite dicas de montagem de deck durante a primeira tentativa. Se possível, anote vida/deck ao fim de cada território ou grave a tentativa para revisão posterior.

## Evidência automática disponível

A amostra com especiais custando 5 teve **8 campanhas completas em 50 runs do bot**; todas as vitórias usaram a estratégia híbrida de defesa/cura. Isso não estima a probabilidade de vitória de uma pessoa. Ver `validacao_especiais_custo5.md` e o relatório bruto correspondente. Resultados antigos refletem regras anteriores; não são todos diretamente comparáveis.
