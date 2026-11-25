# Build web, PWA e hospedagem — Etapa 6

Referência complementar ao [estado atual](estado_atual.md).
Checkpoint da Etapa 5: `4967b58`, branch `feat/web-mobile-port`.

## Gerar a distribuição

~~~powershell
python -m pip install -r requirements-dev.txt -r requirements-web.txt
python -B devtools/build_web.py
# Servidor local e build:
python -B devtools/build_web.py --serve
# Só verificar uma distribuição existente:
python -c "from devtools.web_distribution import verify_distribution; print(verify_distribution('dist/web')['version'])"
~~~

A pasta final é **dist/web/**. Hospede seu conteúdo inteiro, mantendo index.html
na raiz dessa pasta: manifest, ícones, scripts, arquivos web-poc.tar.gz/APK e packs/.
`--dist-dir dist/outro-nome` muda o destino; `--poc` mantém o piloto antigo sem PWA.
Não há backend Python no servidor. HTTPS é necessário, exceto localhost.

O build valida tamanho, SHA-256, inventário do tar e caminhos de todos os pacotes;
release.json lista hashes de todos os arquivos distribuídos. A versão do worker é
derivada do conteúdo. web/runtime-lock.json fixa os 12 recursos externos do runtime
Pygbag 0.9.3/Python 3.12, incluindo WASM, dados, loader e pygame-ce. O build baixa e
confere esse lock em cache local ignorado. Não atualizar hashes para contornar uma
divergência; revisar explicitamente a procedência/versão antes de atualizar o lock.

O primeiro acesso conectado ainda usa a CDN oficial pygame-web. O Service Worker
armazena e verifica esses recursos: as próximas aberturas podem usar somente o
CacheStorage. Não declarar offline pronto com base apenas no cache HTTP.
O Desktop usa sua entrada, dependências e instalador anteriores; não usa este SW.

## Cache e funcionamento offline

- Shell/runtime são preparados antes de ativar o primeiro worker.
- Em segundo plano são preparados 29 pacotes essenciais: introdução, tutorial,
  mapa/gerenciamento, cartas, jogador e habitantes do primeiro território.
- O indicador só anuncia **Offline pronto · território inicial** após confirmar
  todos esses pacotes. É preciso permanecer conectado até essa conclusão.
- Recursos de outros territórios entram no cache ao serem baixados pela primeira
  vez. Offline pronto para o início não significa campanha inteira offline.
- Pacote ausente/interrompido ou com hash inválido não é publicado no cache.
  O jogo informa que precisa de conexão e permite tentar novamente.
- A área de cache é isolada por caminho do aplicativo. Packs têm nomes por hash;
  caches de shell/runtime têm versão. Saves continuam exclusivamente no IndexedDB;
  preferências leves continuam no localStorage. Atualizar o PWA não apaga slots.

Os essenciais somam aproximadamente 151 MiB, além de shell/runtime. Esse preparo
ocorre depois da abertura do menu; não baixa os cerca de 359 MiB de toda a campanha.
O cache pode ser removido pelo navegador/usuário. Use o backup JSON para preservar
e transferir progresso; mudar domínio/origem não transfere o IndexedDB automaticamente.

## Atualizações seguras

O worker novo prepara seu próprio cache e permanece em waiting. Não usa skipWaiting
automaticamente na instalação. ATUALIZAR aparece no menu inicial. Antes de ativar,
todas as abas do mesmo aplicativo precisam confirmar menu sem modal/commit pendente.
Uma aba em combate ou sem resposta adia a atualização. Abas que aprovam bloqueiam
entrada até a troca; depois recarregam. A primeira instalação não recarrega a luta.
Caches de versões antigas são removidos apenas na ativação segura.

## Hospedar e instalar

- **GitHub Pages:** publique o conteúdo de dist/web, incluindo .nojekyll. Caminhos
  de manifesto, start_url, scope, SW e packs são relativos; subpastas são suportadas.
  O id é omitido deliberadamente: a identidade padrão deriva do start_url; um id
  relativo explícito poderia resolver para a raiz da origem e colidir com outro app.
- **Netlify/Vercel:** aponte o diretório público para dist/web; use arquivos estáticos,
  sem fallback de SPA sobre arquivos de packs. _headers traz exemplos para Netlify.
- **itch.io:** compacte o conteúdo com index.html na raiz e envie como jogo HTML.
  A instalação PWA depende de abrir o aplicativo em contexto HTTPS de nível superior;
  o iframe/sandbox do hospedeiro pode limitar Service Worker ou instalação.
- **Android/Chromium PC:** use INSTALAR quando oferecido, ou a opção do navegador.
  install.html é uma entrada leve de instalação, com link para abrir o jogo.
- **iOS:** Compartilhar → Adicionar à Tela de Início. O manifesto solicita paisagem,
  e a camada de rotação permanece como fallback. Chromium emulado não valida Safari
  nem instalação/integração física do iOS.

Sirva service-worker.js e index.html com revalidação/no-cache; packs por hash podem
usar cache longo immutable. Entregue wasm como application/wasm quando hospedado
diretamente. O runtime atual é externo à pasta pública e é cacheado por URL fixada.
Evite remover URLs de packs de uma versão ainda em uso; conserve releases anteriores
até encerrar sessões antigas. Faça deploy atômico da pasta inteira.

## Automação e reprodução dos testes

.github/workflows/build-web.yml gera artefato revisável em PR/push/workflow_dispatch:
instala ferramentas, executa testes isolados, gera e verifica dist/web e publica
o artefato. Não faz deploy automático e não modifica o workflow Windows.

~~~powershell
python devtools/generate_web_campaign_fixtures.py
.venv-web/Scripts/python.exe -m playwright install chromium
.venv-web/Scripts/python.exe devtools/validate_web_pwa.py
python -B devtools/validate_isolated_tests.py --report build/web-stage6-python-tests.json
~~~

O validador abre perfil Chromium temporário, instala/abre/remove o PWA de teste,
usa subpasta /game/, desativa cache HTTP, testa fluxo offline, falhas de pacote e
atualização com duas abas. Ele não usa perfil pessoal nem slots do Desktop.
A instalação real é testada com Chromium completo (channel=chromium), não com o
headless-shell reduzido, que não oferece o domínio de instalação PWA.

Referências: [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers),
[ícones e área segura](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Define_app_icons)
e [protocolo de instalação Chromium](https://chromedevtools.github.io/devtools-protocol/tot/PWA/).

## Resultado da validação — 25/11/2026

Relatório: [validação da Etapa 6](validacao_web_etapa6.json).

- Checkpoint da Etapa 5: `4967b58`.
- **908 testes Python em 88 módulos, zero falhas**, em 205,96 segundos.
- **10 verificações Chromium aprovadas**, incluindo instalação real/abertura
  standalone, subpasta /game/, runtime offline sem cache HTTP, jornada nova e
  tutorial offline, combate, falha/interrupção de pacote e retentativa.
- Atualização permaneceu aguardando durante a luta, foi recusada enquanto outra
  aba lutava e aplicada às duas abas no menu, preservando o save.
- Host mobile 844×390: faixa de status sem cobrir rodapé, alvos de 44×44 e
  bloqueio por orientação aprovados.
- Manifesto sem erros de instalabilidade. O app de teste foi removido após a QA.
- Nenhum arquivo de src/, main.py, dependência nativa ou instalador Windows foi alterado.

Esses testes não comprovam instalação física Android/iOS nem Safari. A execução
do workflow no GitHub e a validação final do instalador pertencem à Etapa 7.

## Fechamento e coexistência com Windows — Etapa 7

O build completo foi regenerado e a suíte final aprovou 909 testes em 89 módulos
(215,39 s). O instalador Windows foi gerado separadamente com Python 3.12.13,
pygame 2.6.1 e PyInstaller 6.11.1, sem Pygbag/Playwright; portátil e instalação
temporária renderizaram o menu. A desinstalação silenciosa preservou dados.
Veja a [arquitetura multiplataforma](arquitetura_multiplataforma.md).

dist/web/, build/, caches, ambientes virtuais e instaladores são saídas locais
ignoradas. Somente fontes, scripts, configurações, ícones e documentação seguem
no commit. O workflow remoto será disparado pelo push; os resultados descritos
aqui são da validação local.

Fechamento cruzado: 11 verificações Web PC, 22 mobile e 10 PWA aprovadas.
Resultados e limites no [relatório final](validacao_multiplataforma_final.json).
