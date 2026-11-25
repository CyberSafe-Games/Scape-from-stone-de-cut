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

## Nitidez e áudio na Web — correção posterior à Etapa 7

A bridge informa tamanho CSS e devicePixelRatio. Apenas SDL/Pygame altera o
backing buffer Web PC: CSS × DPR limitado a 2 e à arte nativa 1920×1080.
Mobile usa o perfil físico 1280×720/DPR 1 do contrato abaixo.
Não atribuir canvas.width/height por JavaScript, pois isso desincroniza SDL e
entrada. Não forçar 960×540 no compacto. O último downscale usa smoothscale;
em 1920×1080 ocorre blit direto, sem redução intermediária. CSS pixelated evita
interpolação borrada quando há ampliação residual. O Desktop mantém WindowManager.

Somente em emscripten, preparar mixer antes dos subsistemas com 44100 Hz,
signed 16-bit, estéreo e buffer 4096. A abertura continua após gesto real;
o backend pode negociar 48000 Hz com o navegador. Quatro canais SFX × ganho
máximo 0,16 e música × 0,25 reservam margem de mix (soma teórica 0,89).
Sliders continuam multiplicativos e desbloqueio/retomada não criam nova trilha
ou ganho master. Não alterar volumes, canais ou inicialização do Desktop.
A medição de PCM no Chromium não substitui escuta em dispositivos físicos.

Validação da correção: **919 testes em 90 módulos, zero falhas** e cinco
verificações de qualidade Chromium aprovadas. A comparação controlada passou
de 33,7 para 32,5 FPS com buffer 2,25 vezes maior; não é garantia de FPS em
aparelhos físicos. [Medições e limites](validacao_web_qualidade.json).

## Mobile com a arte original

Todas as telas mobile usam as cenas originais, sem HUD/menu/grid HTML paralelo.
A camada de toque oferece apenas inspeção artística e confirmação explícita;
os hits invisíveis são ampliados para 44×44 CSS. O buffer mobile é realmente
1280×720, DPR 1, com coordenadas lógicas originais e caches limitados; Web PC e
Desktop mantêm seus caminhos. Laterais recebem a ambientação e o indicador
offline não rouba espaço da cena. Instalação/atualização continua no menu.
Ver [regras, arquitetura e validação](web_mobile.md).

Validação desta correção: **931 testes em 91 módulos, zero falhas**; 14 telas e
11 verificações de toque no Chromium. Combate: 46,3 FPS medianos na emulação;
comparação controlada: 24,6 → 44,2 FPS. Não equivale a medição no celular físico.
Veja o [relatório e limites](validacao_mobile_arte_original.json).

## Memória, backups e hospedagem restrita

O carregador grava os blocos comprimidos em um temporário do MEMFS e calcula
SHA-256 incrementalmente. Libera os bytes JavaScript antes da extração sequencial;
copia cada membro em blocos de 256 KiB e remove o temporário em `finally`. Uma
falha de inventário remove os arquivos parciais e permite tentar novamente.

Após os loaders de combate/tutorial, PNGs de animação já decodificados (e variantes
não usadas daquele kit) são removidos do MEMFS. O grupo fica marcado como
incompleto e é reidratado antes de outro carregamento, usando CacheStorage/cache
HTTP quando disponível. UI/retratos carregados sob demanda, fontes, JSON e OGG
com streaming continuam acessíveis. A troca de contexto remove arquivos do
território anterior. Saves IndexedDB nunca entram nessa limpeza.
Liberar alocações permite reutilizar memória; não faz o heap linear WASM encolher
nem garante ausência de `memory.grow` em qualquer aparelho.

Na seleção de jornadas, **EXPORTAR** e **IMPORTAR** abrem a escolha de um dos três
slots. Exportar baixa JSON v15 compatível com Desktop; importar valida JSON/schema,
versão/migrações, limite de 5 MiB e pede confirmação antes de substituir. A gravação
é confirmada pelo IndexedDB antes da mensagem de sucesso, com revisão/rollback
originais. Faça backups: persistência solicitada não é uma garantia contra limpeza
do navegador. Em iframe com sandbox, o host deve permitir downloads/upload e
armazenamento; o jogo não pode remover essas restrições do site hospedeiro.

A bridge solicita `navigator.storage.persist()` quando disponível e compartilha
a promessa entre PWA/storage. Recusa ou API ausente resulta em `false`, sem
interromper o jogo. `serviceWorker` inacessível ou registro bloqueado em iframe
ativa fallback silencioso: sem indicador de erro/offline pronto, com jogo online e
backups disponíveis. Não prometer instalação/offline nesse contexto. Erros reais
do IndexedDB continuam recebendo tratamento amigável, sem esconder perda de save.

### Tamanhos e auditoria automática

Cada build completo imprime contagem/tamanho e avisos de hospedagem, além de
gravar `build/web-hosting-audit.json` (não versionado). Não adiciona arquivos de QA
a `dist/web/`, preservando o inventário de integridade. Build medido:

| Parcela | Bytes | MiB |
|---|---:|---:|
| Pacote inicial Python/assets | 6896564 | 6.58 |
| 71 pacotes da campanha sob demanda | 376144379 | 358.72 |
| Inicial + pacotes | 383040943 | 365.30 |
| Distribuição completa em disco (shell, APK auxiliar, scripts e metadados incluídos) | 391020849 | 372.91 |

São **93 arquivos**, maior arquivo **8.31 MiB**;
nenhum limite auditado foi excedido. Os valores históricos de ~6,56 MiB +
~358,72 MiB (~365 MiB) representam apenas inicial + pacotes; não são o tamanho
completo da pasta distribuída nem o download obrigatório da abertura. O runtime
externo fixado no lock soma 21.90 MiB e é cacheado
separadamente pelo navegador; não foi somado ao tamanho do diretório hospedado.

Limites verificados em 25/11/2026:

- [Cloudflare Pages](https://developers.cloudflare.com/pages/platform/limits/):
  25 MiB por arquivo e 20.000 arquivos no Free (planos pagos permitem 100.000).
  Não há teto agregado em bytes publicado nessa página; não inventar um limite.
- [itch.io HTML5](https://itch.io/docs/creators/html5#zip-file-requirements):
  1.000 arquivos, 240 caracteres por caminho, 200 MB por arquivo e 500 MB no
  conteúdo extraído do ZIP. O auditor usa MB decimal de forma conservadora.

O aviso não impede build local; corrija os excessos antes de hospedar. Inclua
`index.html` na raiz do ZIP do itch.io, sem diretório pai. Preserve os bytes dos
`.tar.gz` e hashes: alguns CDNs aplicam `Content-Encoding: gzip` automaticamente;
confira os headers no host final para não entregar um tar já descomprimido ao
carregador que espera gzip. A validação local não comprova um deploy no itch.io
ou Cloudflare. As regras de HTTPS, caminhos relativos e publicação atômica acima
continuam valendo.

Validação desta entrega: **942 testes / 92 módulos, zero falhas**; 6 verificações
iframe/backup, 10 PWA/offline e 14 telas mobile aprovadas no Chromium. Primeiro
combate: 38.451.166 bytes (36,67 MiB) removidos do MEMFS, temporário já removido.
Resultados e limites no [relatório das blindagens](validacao_web_blindagens.json).

Para repetir o teste de iframe, mantenha o servidor local de `dist/web` na porta
8765 e execute `.venv-web/Scripts/python.exe devtools/validate_web_hardening.py`.
O script cria outra origem HTTP local temporária e perfil Chromium isolado; não
usa slots pessoais nem publica em serviços externos.
