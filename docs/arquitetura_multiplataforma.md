# Arquitetura multiplataforma

Referência complementar ao [estado atual](estado_atual.md).
Este documento descreve a entrega das Etapas 1–7, sem substituir as regras
de combate/cartas/saves dos demais contratos.

## Três modos coexistentes

| Modo | Entrada/execução | Tela e entrada | Persistência |
|---|---|---|---|
| Desktop nativo | main.py, Pygame, loop síncrono | Canvas 1920×1080; mouse/teclado, F10/F11 | JSON v15 em disco |
| Web PC | web/main.py → web/campaign.py, Pygbag/WASM e asyncio | Mesmo layout proporcional; hover, roda, teclado e botão fullscreen | IndexedDB v15; preferências no localStorage |
| Web mobile/PWA | Mesmo build web com host compacto | Coordenadas 1920×1080, buffer físico 1280×720/DPR 1, arte original, toque/inspeção e paisagem | Mesmo IndexedDB; CacheStorage somente para recursos |

O Desktop não instala Pygbag nem Playwright para executar ou empacotar.
O instalador usa assets originais; não inclui dist/web nem seu runtime/cache.
Na fonte, saves/configurações mantêm seus caminhos locais do projeto.
No executável, dados graváveis ficam em %LOCALAPPDATA%/ScapeFromStoneDeCut;
assets são somente leitura, resolvidos por _MEIPASS.

## Fronteiras compartilhadas

- src/platforms: capacidades, recursos, dados graváveis, janela e encerramento.
- src/storage: DiskStore atômico (temporário/fsync/replace) e BrowserStore/IndexedDB.
- src/systems e src/models: mesmas cartas, estados, campanha, revisões e regras.
- src/core/application.py: um frame comum; desktop síncrono e web cooperativa.
- src/core/input_router.py e InspectionController: entrada e inspeção separadas.
- Web usa cenas nativas com adaptadores de confirmação e carregamento por contexto.
  Transações só confirmam a UI depois do commit real; falhas mantêm/restauram o estado.
- web/mobile.py/.js adaptam apresentação e seleção, sem duplicar regras econômicas.
- CacheStorage não guarda saves. Exclusão de cache não deve zerar o IndexedDB.

## Desktop: execução, build e verificação

Para empacotar com PyInstaller 6.11.1, use Python **3.12 ou 3.13 x64**;
Python 3.14 não é suportado por essa versão do empacotador.
O runtime fonte e o ambiente de build são separados.

~~~powershell
py -3.12 -m venv .venv-build
.venv-build/Scripts/python.exe -m pip install -r requirements.txt -r requirements-build.txt
installer/build_installer.bat
~~~

O batch prefere .venv-build existente, valida a versão e usa Inno Setup 6,
encontrado no PATH ou em seus diretórios de instalação conhecidos.
Saídas: dist/ScapeFromStoneDeCut/ e ScapeFromStoneDeCut-Setup-0.1.0.exe
(versão do arquivo VERSION). Não alterar VERSION apenas para um teste local.

A entrada normal mantém o comportamento anterior. O modo técnico abaixo renderiza
quatro quadros do menu, grava relatório/PNG e encerra; não joga nem abre slots.
Preferências do smoke ficam isoladas junto ao relatório.

~~~powershell
python main.py --smoke-report build/native-check.json
dist/ScapeFromStoneDeCut/ScapeFromStoneDeCut.exe --smoke-report build/frozen-check.json
python devtools/validate_windows_build.py --iscc "C:/caminho/Inno Setup 6/ISCC.exe"
~~~

O validador recompila pelo batch oficial, confirma ausência de dependências web,
exercita o executável portátil e instala/desinstala em pasta temporária.
Se já houver instalação pessoal registrada, não a substitui: registra a omissão
desse trecho. A desinstalação com /SUPPRESSMSGBOXES preserva saves por padrão;
a confirmação interativa permanece disponível.

## Web: execução e distribuição

~~~powershell
python -m venv .venv-web
.venv-web/Scripts/python.exe -m pip install -r requirements-web.txt
.venv-web/Scripts/python.exe devtools/build_web.py
.venv-web/Scripts/python.exe devtools/build_web.py --serve
~~~

A pasta publicável é dist/web/. O servidor local usa http://127.0.0.1:8765.
O build padrão contém toda a campanha em pacotes por contexto. --poc reproduz
o piloto limitado das primeiras etapas.

PWA: manifesto e ícones oficiais, runtime fixado por hashes, cache inicial do
território 1 e recursos adicionais sob demanda. Uma atualização permanece em
waiting durante a luta; todas as abas precisam confirmar menu sem gravações
pendentes antes de ativar. HTTPS é necessário fora de localhost.
Veja o [guia completo de build/hospedagem](build_web.md) e os contratos de
[plataforma](web_platforms.md), [persistência](web_storage.md),
[campanha](web_campaign.md) e [toque/layout](web_mobile.md).

## Higiene e validação

build/, dist/, ambientes virtuais, bytecode, caches do Pygbag, instaladores e
_arquivos_antigos_para_deletar/ ficam ignorados. PNGs de ícones em web/icons são
fontes necessárias e versionadas; screenshots/logs de QA ficam somente em build/.
Não executar git add global: revisar e adicionar os arquivos da entrega explicitamente.

~~~powershell
python -m pip install -r requirements-dev.txt
python -B devtools/validate_isolated_tests.py --report build/final-tests.json
python -B devtools/audit_project_docs.py --output build/final-docs.json
~~~

A integração em GitHub usa workflows separados para Windows e Web.
O workflow web produz artefato estático revisável; não publica o site automaticamente.
Os relatórios por etapa são históricos. A conferência em Chromium não comprova
Safari/iOS físico nem uma campanha completa jogada no instalador.

