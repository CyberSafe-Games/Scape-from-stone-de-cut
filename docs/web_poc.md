# Prova Web — Etapa 1

> Documento vigente desta prova. Mecânicas canônicas: [estado atual](estado_atual.md).

## Escopo

Menu existente e batalha real contra Slime: cartas iniciais, animações, intenção,
dano, defesa, Veneno e desfechos. ESC/MENU retorna à prova; R reinicia após o
desfecho. Opções, campanha, slots e recompensas persistentes estão fora da prova.
As preferências são temporárias. Não há localStorage, IndexedDB, PWA nem layout mobile.

## Execução

Use um ambiente separado do desktop:

~~~powershell
python -m venv .venv-web
.venv-web/Scripts/python.exe -m pip install -r requirements-web.txt
.venv-web/Scripts/python.exe devtools/build_web.py
.venv-web/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory build/web-poc/build/web
~~~

Abra http://127.0.0.1:8765. O menu abre sem gesto; o clique em Iniciar libera o áudio e prepara o combate.
O build depende de Internet para baixar o runtime Pygbag e a fonte licenciada OFL.
A página resultante também depende do CDN de runtime: ainda não é uma PWA offline.

O build seleciona recursos por lista explícita, sem copiar assets inteiros.
O menu prepara somente fontes e fundo; recursos da luta são preparados em lotes
após Iniciar. O pacote da prova ainda transfere esses recursos juntos.
Não confundir carregamento diferido em memória com download por território.
O manifesto gerado registra bytes, arquivos e origem/hash da fonte Noto.

## Validação

~~~powershell
.venv-web/Scripts/python.exe -m playwright install chromium
.venv-web/Scripts/python.exe devtools/validate_web_poc.py
python -B devtools/validate_isolated_tests.py --report build/web-poc-python-tests.json
~~~

Capturas, log e métricas do navegador ficam em build/web-poc-validation.
Medições de FPS em Chromium automatizado são específicas do ambiente e não
equivalem a validação em celular ou garantia de 60 FPS. Nenhum save real é usado.

## Limites de integração

main.py mantém a entrada desktop e finalização de disco original. Application
compartilha somente eventos/update/draw; o caminho web é cooperativo e retorna
sem encerrar o interpretador. O instalador e SaveManager v15 não foram alterados.
A Etapa 2 precisa ser aprovada separadamente.

## Medição da prova — 25/11/2026

Chromium 159.0.8154.6 automatizado, sem limitação artificial de rede/CPU,
viewport 1280×720. Python WASM 3.12.12/pygame-ce 2.5.7; desktop validado
com Python 3.14.5/pygame-ce 2.5.8. Não é validação de Safari/mobile.

| Métrica | Observado |
|---|---:|
| Recursos selecionados | 170 arquivos |
| Assets selecionados, sem compressão | 22.88 MiB |
| Pacote tar.gz do jogo | 21.73 MiB |
| Tráfego observado, incluindo runtime/CDN | 32.21 MiB |
| Navegação até menu | 5.00 s |
| Iniciar até combate disponível | 1.08 s |
| FPS do menu na amostra | 60.0 |
| FPS mediano em combate | 28.6 |
| Menor amostra do combate | 19.4 |
| Heap WASM reservado ao final | 368.75 MiB |

Heap reservado não mede memória viva dos sprites nem memória total do processo.
surfaces_bytes cobre somente as sequências de atores/cartas carregadas.

Vitória por cinco cliques de ataque (inimigo 0 HP, jogador 53 HP); derrota em
partida separada encerrando turnos sem atacar; retorno ao menu confirmado.
Hover de carta e intenção capturados. Menu abre com mixer bloqueado; o clique
em Iniciar libera mixer e trilha, sem desativar a política de autoplay do browser.
Não houve avaliação auditiva humana. localStorage permaneceu vazio.

A composição estática custava aproximadamente 78 ms/quadro. O cache exclusivo
da prova reduziu esse trecho para 1–2 ms, preservando pixels conforme teste.
O combate funciona sem congelar a aba; não atingiu 60 FPS constantes.
Não inferir desempenho mobile ou da campanha completa a partir desta prova.

Suíte integral sem retomada: **790 testes / 83 módulos,
zero falhas**, em 183.93 s. Inclui os 781 testes anteriores e nove
novos casos de execução cooperativa, isolamento, áudio, seleção de recursos e caches.
O inventário agora também reconhece AsyncFunctionDef.

[Relatório técnico completo](validacao_web_poc.json).
