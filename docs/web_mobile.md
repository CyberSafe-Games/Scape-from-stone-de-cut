# Mobile com arte original e toque

Referência complementar ao [estado atual](estado_atual.md).
Branch: feat/web-mobile-port. Esta regra substitui a apresentação compacta
da Etapa 5 e a regra de HiDPI mobile anterior.

## Uma única composição em todas as telas

Menu, slots, mapa, combate, recompensa, loja, mochila, altar, configurações,
guias, quadrinhos e epílogo usam as cenas Pygame originais. Não reconstruir
HUDs, cartas da mão, listas, botões ou barras de vida em painéis HTML.
O canvas mantém enquadramento 16:9 completo, sem cortar rodapé/retratos.
Telas mais largas mostram a própria ambientação nas laterais; não esticar
nem cortar a composição para preencher a proporção 19,5:9.

web/mobile.js apenas encaminha toque e mostra a carta artística selecionada
com a confirmação flutuante. Não desenha header/grid/footer paralelos.
Os PNGs de cartas continuam vindo de AssetManager, com custo e nível reais.
Intenções com arte dedicada preservam essa arte e regras; ações comuns sem
PNG ganham uma carta composta com moldura e retrato originais.

## Interação sem alterar regras

- Primeiro toque inspeciona. JOGAR, COMPRAR, EQUIPAR, REMOVER, APRIMORAR ou
  ESCOLHER confirma. A inspeção não gasta energia, ouro ou recompensa.
- Mochila conserva as abas, slots e coleção originais; a paginação não é
  substituída por outro layout. Altar mantém sua comparação nativa e oferece
  ANTES/DEPOIS na inspeção.
- Menus, mapa, sliders, modais e guias recebem eventos dos handlers originais.
  Apenas a área invisível de hit cresce para pelo menos 44×44 CSS.
- Comandos carregam época e geração. Descartar toques antigos, duplos commits,
  gestos cancelados e ações durante gravação. Troca de imagem ANTES/DEPOIS é
  neutra; não deve consumir o registro da confirmação seguinte.
- Rotação em aparelhos touch pausa em retrato; blur/visibilitychange cancela
  seleção/arraste e congela o ActiveTimeline. Web PC amplo mantém mouse/hover.
- O indicador PWA não ocupa espaço no mobile. Instalar/atualizar fica disponível
  discretamente no menu inicial; aplicação da atualização mantém a coordenação
  segura entre abas. O aviso de atualização em curso ainda pode bloquear a UI.

## Renderização real em 1280×720

A viewport compacta/touch usa MobileCanvas com armazenamento físico **1280×720**
e DPR de apresentação **1**. As coordenadas lógicas permanecem 1920×1080 para
reutilizar integralmente a arte e os handlers. Não desenhar primeiro um quadro
Full HD para só depois reduzi-lo: blits e primitivas vão diretamente ao buffer
720p. A apresentação é um blit direto. Web PC conserva o backing por CSS × DPR
limitado a 2/1920×1080; Desktop conserva WindowManager e mixer nativo.

drawing_coordinates adapta primitivas somente durante o draw síncrono mobile e
restaura as funções em finally. Superfícies auxiliares comuns não têm coordenadas
alteradas. Cópias/subsuperfícies para composições antigas são materializadas nas
coordenadas lógicas; suas camadas estáticas são preparadas uma vez.

Artes imutáveis escaladas têm LRU de 24 MiB; textos têm cache de 8 MiB.
Não congelar camadas mutáveis como preenchimento de HP. Alpha global é aplicado
no blit sem refazer o resize. Limpar composições ao sair do perfil compacto,
evitando reutilizar uma composição de baixa resolução no Web PC.
Partículas procedurais ficam limitadas a **3 por emissão / 12 por frame**.
Sprites, dano, energia, turnos e persistência v15 não mudam.

## Validação

~~~powershell
python devtools/generate_web_campaign_fixtures.py
.venv-web/Scripts/python.exe devtools/build_web.py --serve
# Em outro terminal:
.venv-web/Scripts/python.exe devtools/validate_web_mobile_art.py
.venv-web/Scripts/python.exe devtools/validate_web_management.py
python -B devtools/validate_isolated_tests.py --report build/mobile-art-tests.json
~~~

Checkpoints e screenshots ficam em build/; não gravar nos slots pessoais nem
versionar artefatos de QA. Os relatórios das Etapas 5–7 são históricos; consulte
o [relatório desta correção](validacao_mobile_arte_original.json). Meta de desempenho: 45–60 FPS.
Emulação Chromium não comprova FPS em um celular físico, Android ou Safari/iOS.

A persistência e a liberação de recursos por contexto seguem os contratos de
[persistência](web_storage.md) e [campanha](web_campaign.md).

Validação desta correção: **931 testes em 91 módulos, zero falhas**; 14 telas e
11 verificações de toque no Chromium. Combate: 46,3 FPS medianos na emulação;
comparação controlada: 24,6 → 44,2 FPS. Não equivale a medição no celular físico.
Veja o [relatório e limites](validacao_mobile_arte_original.json).
