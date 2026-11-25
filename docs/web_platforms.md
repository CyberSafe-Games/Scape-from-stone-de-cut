# Plataformas e renderização web — Etapa 2

> Referência vigente. Regras do jogo: [estado atual](estado_atual.md).
> Escopo inicial/execução: [prova web](web_poc.md).

## Fronteiras

src/platforms/capabilities.py detecta emscripten explicitamente. DesktopPlatform
resolve recursos (_MEIPASS) e dados do usuário (LOCALAPPDATA no executável;
raiz no modo fonte). WebPlatform mantém recursos no pacote e separa um caminho
de sessão /tmp/scape-from-stone-session: não é armazenamento durável.

WindowManager nativo conserva monitor, modos, F10/F11, mouse e letterbox.
create_window_manager seleciona WebWindowManager na web, sem consultar monitor.
O canvas conserva coordenadas 1920x1080 e saída 1280x720 proporcional via CSS.
Fullscreen API fica na bridge DOM e só é acionada por gesto; erros são tratados
sem rejeição não observada. O estado acompanha fullscreenchange.

SceneManager.request_exit substitui encerramento direto nas cenas. Desktop
solicita parar o loop, que mantém a finalização/salvamento existente. Web retorna
à home_factory; se não houver tela inicial, termina o loop sem SystemExit.

## Foco e tempo

A bridge acompanha visibilitychange/focus/blur e uma geração de retomada.
Application não atualiza/desenha nem processa entrada de jogo enquanto inativo;
áudio é pausado sem reiniciar as faixas. Ao retornar, o primeiro dt é zero e
eventos antigos são descartados. A geração evita compensar o tempo oculto mesmo
se nenhum quadro Python tiver rodado durante a suspensão.

## Otimizações e fidelidade

- Cenário/vinheta/sombras estáticas do combate passam a um cache compartilhado,
  invalidado por cenário, andar e dimensões. Não inclui atores nem partículas.
- Escalas de cartas e variações discretas da respiração usam cache por imagem.
- Blits dos atores processam apenas sua caixa alfa. A âncora do canvas original
  e os modos alpha/premultiplicado são preservados.
- Destino da apresentação web é reutilizado a cada quadro, sem reduzir o canvas.
- Na prova Slime, a bandeja é composta em RGB sobre o fundo estático. Cartas,
  personagens e textos continuam dinâmicos; Ultimates usam o caminho normal
  porque seus efeitos podem cruzar a região. Não generalizar esse atalho para
  outros encontros sem validar a sobreposição de efeitos.
- Testes comparam pixels para escalas, alpha, premultiplicação e bandeja em
  repouso/ataques. Fontes, sprites, qualidade e resolução desktop são mantidos.

Não há IndexedDB, backend de save web, PWA ou layouts compactos nesta etapa.
O schema v15 e os arquivos do instalador não foram alterados.

## Resultado — 25/11/2026

| Verificação | Resultado |
|---|---|
| Combate Chromium, mediana | 52.1 FPS |
| Referência da Etapa 1 | 28.6 FPS |
| Ganho observado | 82.1% |
| Menor amostra | 31.9 FPS |
| Fullscreen API | Entrada e saída aprovadas |
| Pausa, áudio e retomada | Aprovados por eventos DOM; sem compensar tempo oculto |
| Saída da prova | Retorna ao menu, sem SystemExit |
| Suíte integral | 808 testes / 84 módulos, zero falhas |
| Duração | 202.50 s, execução sem retomada |

Mesmo Chromium 159 e viewport 1280x720 da referência, sem throttling artificial.
Não interpretar essa medição como 60 FPS constantes nem como validação mobile.
Na execução headless, a segunda aba continuou visível: a checagem de
visibilitychange usou override DOM de document.hidden, além do teste de
focus/blur. O relatório registra explicitamente essa limitação.

Amostra equivalente em vitória: bandeja caiu de aproximadamente 7,5 para
0,3 ms e desenho do jogador de 3,7 para 0,3 ms. O desenho total da amostra
caiu de 20,8 para 10,6 ms. Valores por trecho são amostras, não médias da luta.

Os 790 testes anteriores continuam aprovados e foram adicionados 18 casos.
O teste antigo de saída foi atualizado para exigir request_exit e proibir
pygame.quit dentro da cena. Testes de pixels cobrem transparência, escala,
fundo, invalidação por andar e bandeja durante ataques.
[Relatório detalhado](validacao_web_etapa2.json).

## Arquivos da Etapa 2

Criados:
- src/platforms/__init__.py, capabilities.py, desktop.py e web.py.
- src/core/web_window.py e src/ui/render_cache.py.
- web/bridge.js e tests/test_platform_services.py.
- docs/web_platforms.md e docs/validacao_web_etapa2.json.

Modificados sobre a Etapa 1:
- main.py e src/config/settings.py.
- src/core/application.py, scene_manager.py, window.py e audio_manager.py.
- src/scenes/menu_scene.py e battle_scene.py.
- src/ui/card_view.py e entity_view.py.
- web/poc.py, web/styles.css e devtools/build_web.py/validate_web_poc.py.
- tests/test_audio_ui.py e tests/test_web_proof.py.
- README.md, AGENTS.md, docs/estado_atual.md, documentacao_manifest.json e inventario_testes.json.


A persistência descrita como pendente nesta validação da Etapa 2 foi implementada
na [Etapa 3](web_storage.md); o FS virtual continua restrito à sessão.
