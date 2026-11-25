# Persistência híbrida — Etapa 3

Contrato complementar ao [estado atual](estado_atual.md). Branch de trabalho:
`feat/web-mobile-port`. O formato de save continua **v15**; a versão **1** do
banco IndexedDB é independente do schema do jogo.

## Backends e integridade

- Desktop: `DiskStore` mantém JSON UTF-8, arquivo temporário, flush, fsync e
  os.replace, nos caminhos locais já existentes. Preferências locais e instalador
  Windows permanecem no fluxo nativo.
- Web: `BrowserStore` usa `web/storage.js`; IndexedDB guarda os slots, perfil,
  run e combat_snapshot. Saves legados são preservados no object store backups
  quando convertidos no primeiro commit. Não guardar slots no localStorage.
- A fronteira Python/JavaScript usa JSON com escapes ASCII para preservar acentos
  e nomes de cartas ao longo de sucessivos commits e backups.
- Apenas preferências leves de GamePreferences vão para localStorage, passando
  pela mesma sanitização do desktop. Bloqueio desse storage avisa que ajustes
  valem somente durante a sessão.
- Revisão comparada dentro da transação readwrite, incluindo verificação da run
  de origem para impedir sobrescrita após exclusão/recriação do slot em outra aba.
  Conflito exige recarregar; nunca mesclar silenciosamente duas runs.
- Solicitar durabilidade strict quando suportada; fallback para a transação
  padrão do navegador. Somente IDBTransaction.oncomplete confirma a operação.
- Importação limitada a 5 MiB, JSON de dados, mesma migração/validação v15;
  recusa versões futuras e pede confirmação para substituir slot ocupado.

## Comandos e confirmação visual

1. A interface agenda um comando com SceneManager.submit. Entrada de jogo fica
   bloqueada enquanto a gravação está pendente; desenho e asyncio continuam.
2. BrowserSaveManager cria uma candidata isolada e um StagedStore. Reutiliza
   SaveManager e as regras existentes de Loja, Altar, Mochila, guias e recompensas.
3. A candidata é enviada ao IndexedDB com revisão esperada; toda a gravação e o
   backup legado compartilham uma única transação.
4. Após oncomplete, atualiza o espelho e publica a candidata no estado da cena.
   Só então aparecem aquisição, melhoria, confirmação de deck ou navegação.
5. Em falha, a candidata é descartada. A versão confirmada fica intacta; o
   combate restaura seu último snapshot confirmado. Não há sucesso antecipado.

O método síncrono save do manager web recusa chamadas diretas: não usar uma
gravação de sessão como se fosse persistência durável. O desktop continua
síncrono e usa o transact original com rollback.

## Checkpoints e backup

O piloto grava mudanças lógicas do combate e estados de vitória/derrota;
não grava por frame de animação. Recarregar restaura pilhas, energia, vida,
efeitos, plano de ações e estado aleatório do snapshot confirmado.
Recompensas usam as mesmas regras e identificadores idempotentes da campanha.

pagehide e visibilitychange solicitam checkpoint adicional; eventos de fechamento
não garantem tempo de escrita. A proteção principal são os commits após cada
comando e os checkpoints lógicos já confirmados, não um save tardio ao fechar.

EXPORTAR/IMPORTAR na seleção de saves usa arquivo .json: diálogo nativo no
desktop e download/seletor de arquivo no navegador. Não equivale a sincronização
em nuvem. Cada origem (protocolo, host e porta) possui seus próprios dados.
O botão de proteção de dados solicita navigator.storage.persist(); se negado,
o jogo informa a necessidade de manter backup. O navegador pode apagar dados
sem essa garantia ou por limpeza manual do usuário.

## Escopo e reprodução

O build padrão abre um menu persistente, três slots e um acesso de validação às
telas reais da Loja, Mochila, Altar, Configurações e a um combate com Slime.
A campanha completa e os layouts mobile pertencem às próximas etapas.
O parâmetro `?render=1` conserva o piloto de renderização sem saves das Etapas 1/2.
Assets de gerenciamento entram no pacote sob demanda do build; não incluir saves
locais, backups do jogador, ambientes Python ou arte da campanha inteira.

```powershell
.venv-web/Scripts/python.exe devtools/build_web.py
.venv-web/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory build/web-poc/build/web
# Em outro terminal; Chromium/Playwright no ambiente web:
.venv-web/Scripts/python.exe devtools/validate_web_storage.py
python -B devtools/validate_isolated_tests.py --report build/web-stage3-python-tests.json
```

O validador usa contexto Chromium isolado e um JSON nativo temporário, sem acessar
saves reais. Exercita recarga, compra confirmada, clique duplo, falha de quota,
conflito de abas, Mochila, Altar, guias, preferências, exportação/importação,
snapshot e indisponibilidade de IndexedDB. Relatórios e capturas ficam em
`build/web-storage-validation/`.



## Resultado da validação — 25/11/2026

- Suíte completa: **831 testes, 85 módulos isolados, zero falhas**.
- Novos contratos de armazenamento: **23 testes**, incluindo confirmação,
  revisão, rollback, migração v15, preferências e preservação de acentos.
- Conferência final direcionada: **67 testes aprovados**.
- Chromium 159.0.8154.6: **19 verificações aprovadas**. Incluem slots e recarga,
  compra confirmada, clique duplo, quota/rollback, Mochila, Altar, guias,
  preferências, duas abas, Unicode, exportação/importação, checkpoint e rollback
  de combate, recompensa sem duplicação, morte/perfil, nova run, solicitação de
  persistência, migração com backup e IndexedDB indisponível.

A lista completa de arquivos criados/alterados e as evidências por módulo estão
no [relatório da Etapa 3](validacao_web_etapa3.json). O schema v15, os caminhos
nativos e os arquivos do instalador foram preservados. Nenhum asset foi movido
ou excluído nesta etapa. Não houve commit, push ou merge.

