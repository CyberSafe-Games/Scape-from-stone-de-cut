# Layout compacto e entrada por toque — Etapa 5

Referência complementar ao [estado atual](estado_atual.md).
Checkpoint da Etapa 4: `62de681`, branch `feat/web-mobile-port`.

## Limites de plataforma

O Desktop continua com seu controlador, canvas virtual 1920×1080, mouse e teclado.
Apenas o host da campanha web instala MobileInterface. A viewport web útil abaixo
de 1000 px de largura ou 600 px de altura ativa controles compactos. Dispositivos
com apontador primário por toque também usam esses controles em tablets amplos. O buffer
Pygame acompanha o tamanho CSS do canvas multiplicado pelo DPR (teto 2), limitado
a 1920×1080, preservando as coordenadas internas e controles em viewports amplas.

O fragmento web/index.html é injetado no bootstrap gerado por Pygbag. Não substituir
o bootstrap inteiro: web/styles.css, bridge.js e mobile.js compõem o host.
Safe areas usam env(safe-area-inset-*), viewport-fit=cover e altura dinâmica.
Dispositivos de toque em retrato exibem "Gire o aparelho para continuar".
Foco/visibilidade e orientação bloqueiam entrada, updates e desenho. ActiveTimeline
congela também pygame.time.get_ticks no runtime web; a retomada descarta o intervalo
suspenso e gestos antigos, sem avançar timers de animação.

## Interação e apresentação

A camada compacta reutiliza as ilustrações existentes e PNGs produzidos pelo mesmo
AssetManager, com custo real e nível da cópia. Não cria regras paralelas de combate,
inventário ou preços. O HTML usa textContent para descrições, sem interpretar
strings do save como marcação.

- Primeiro toque em carta/Ultimate abre inspeção. JOGAR confirma explicitamente.
- Intenções e status abrem descrição legível; FECHAR ou toque no fundo dispensa.
- Compra, equipamento, remoção e recompensa exigem seleção seguida de confirmação.
- Mochila separa Reserva, Equipado e Ultimates; reserva e ofertas reduzem paginação.
- Altar compara as descrições reais de LV1/LV2 antes de evoluir somente a cópia.
- Configurações oferecem abas e área rolável, ranges e botões −/+ de volume.
- Botões têm alvos CSS mínimos de 44×44; imagens preservam contain e padding.
- Guias usam seus textos/flags/transações existentes. O spotlight compacto é
  calculado com o elemento DOM atual, acompanhando rotação, abas e rolagem.

MobileInterface registra callbacks da cena atual, associadas à época da composição
e geração de orientação/foco. Comandos repetidos, obsoletos ou recebidos durante
commit pendente não executam. O canvas compacto não recebe eventos sintéticos
touch+mouse. Cancelamento limpa seleção e arraste; o Web PC amplo conserva seus
eventos de mouse, hover, roda e teclado.

## Perfil leve e persistência

O perfil compacto limita partículas procedurais compartilhadas a seis por emissão e 24 por frame.
Não muda sprites, dano ou cadência de combate. A camada de prévias usa cache limitado
de 48 entradas, descartado ao mudar de cena/modal. A liberação dos recursos e caches
por contexto continua sob responsabilidade de CampaignAssets.
IndexedDB e confirmações/rollback permanecem os mesmos da Etapa 3.

## Reprodução

~~~powershell
.venv-web/Scripts/python.exe devtools/build_web.py --serve
# Outro terminal:
.venv-web/Scripts/python.exe devtools/validate_web_mobile.py
python -B devtools/validate_isolated_tests.py --report build/web-stage5-python-tests.json
~~~

A emulação Chromium usa toque real de Playwright, viewports Android/iPhone e
checkpoints QA v15 declarados. Não equivale a medição em Android/Safari/iPhone
físicos. PWA, offline e distribuição pertencem à Etapa 6.

## Validação final — 25/11/2026

Relatório: [resultados da Etapa 5](validacao_web_etapa5.json).

- Checkpoint da Etapa 4: `62de681`; alterações da Etapa 5 locais na mesma branch.
- Suíte completa: **889 testes, 87 módulos, zero falhas**, em 181,28 segundos.
  Conferência final direcionada: **67 testes aprovados**.
- Chromium: **11 verificações por viewport**, Android 915×412 e iPhone 844×390.
  Rotação, congelamento/retomada, foco, cancelamento de seleção, Ultimate,
  combate/recompensa, Loja, Mochila, Altar e preferências após F5 aprovados.
- Web PC amplo: **11 verificações aprovadas** com mouse, roda, teclado, sliders
  e persistência. Mediana observada na Loja: **58,66 FPS**.
- FPS mediano do combate de QA: **41,50** no viewport Android e **35,66** no iPhone.
- Heap WASM reservado: **442,50 MiB** em ambos; amostra de heap JS ao final:
  **179,29 MiB** em ambos. Heap reservado não equivale a RSS.
- Build inicial: **6,57 MiB**, mantendo os recursos da campanha sob demanda.
- O instalador Windows e os requisitos nativos não foram alterados; nenhum
  asset foi substituído ou movido nesta etapa.

A medição usa Chromium no computador, DPR 1, sem limitação de CPU/rede, e um
combate Slime com checkpoint QA v15. Não mede a campanha completa em celular
físico, Android real ou Safari/iOS. A Etapa 6 ainda não foi iniciada.

