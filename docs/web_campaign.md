# Campanha Web PC — Etapa 4

Referência complementar ao [estado atual](estado_atual.md).
Checkpoint anterior: `742218f`, na branch `feat/web-mobile-port`.
O Desktop e o instalador Windows continuam independentes do build web.

## Recursos e carregamento

`devtools/build_web.py` gera a campanha completa por padrão. O manifesto
`web_manifest.json` atribui cada recurso ativo a um único grupo. Os pacotes
possuem hash SHA-256, arquivos permitidos e URLs por conteúdo; o pacote inicial
contém fontes, fundo e recursos do menu. A licença/fonte de símbolos empacotada
continua incluída. Os recursos são servidos como arquivos estáticos, sem backend.

Grupos: menu; gerenciamento/mapa; jogador/efeitos; áudio; território; inimigo;
introdução; pós-tutorial; epílogo. A dupla Alvar/Tekks compartilha o contexto das
duas fases. Todos os habitantes do bioma atual são preparados antes do sorteio
nativo de inimigos, evitando que o resultado aleatório escolha arte ausente.

`CampaignAssets` baixa e verifica os pacotes cooperativamente, valida os
caminhos de extração, carrega somente os kits necessários e descarta arquivos
e superfícies de contextos anteriores. O carregamento tem barra de progresso,
mensagem de contexto e nova tentativa em caso de falha. Não considerar uma
troca de tela concluída antes do carregamento. Não baixar toda a campanha na
abertura da página.

Hospedar os pacotes com Cache-Control immutable e URLs com hash; deixar
index.html sem cache permanente. A memória linear WASM pode manter seu máximo
de alocação mesmo após liberar superfícies; avaliar reutilização/estabilização,
não exigir que o heap diminua fisicamente após cada tela.

## Cenas, regras e persistência

As cenas web herdam as cenas nativas: Menu, seleção de slots, Tutorial, Mapa,
Batalha e Cutscene. Loja, Mochila, Altar e Configurações reutilizam as telas
existentes. A adaptação fica em `web/campaign.py`: regras de dano, preços,
progressão, drops e duração das animações permanecem nas fontes atuais.

A confirmação de comandos mantém o contrato da
[persistência híbrida](web_storage.md): candidata isolada, revisão no IndexedDB,
publicação apenas após oncomplete e rollback. Tutorial/introdução/guias,
recompensas, nova run e retorno ao mapa aguardam confirmação real.
A vitória final confirma o progresso antes de abrir o epílogo.

## Entrada e inspeção

`InputRouter` conserva os eventos nativos e expõe coordenadas virtuais,
botão, tecla e os dois eixos da roda sem reescrever event.pos. As cenas
continuam com a mesma interpretação de mouse/teclado. A roda também navega
pelas páginas da Loja e do Altar no navegador.

`InspectionController` separa o alvo inspecionado do desenho. Suporta hover,
limpeza, inspeção fixada para extensão futura e preview limitado ao viewport.
As intenções usam esse controlador sem trocar a identidade das cartas.

O botão MENU centralizado, botões de navegação, controles de configurações e
o botão DOM de tela cheia fornecem alternativas aos atalhos interceptados
pelo navegador. Cutscenes têm PULAR / CONTINUAR visível. Não bloquear teclas
globais do navegador. Mobile, touch e PWA continuam fora desta etapa.

## Reprodução e cobertura de QA

```powershell
.venv-web/Scripts/python.exe devtools/build_web.py --serve
# Em outro terminal:
python devtools/generate_web_campaign_fixtures.py
.venv-web/Scripts/python.exe devtools/validate_web_campaign.py
python -B devtools/validate_isolated_tests.py --report build/web-stage4-python-tests.json
```

O piloto anterior continua disponível com `devtools/build_web.py --poc`;
a sua seleção limitada de recursos não define os limites da campanha completa.

A validação automatizada distingue dois casos: criação de slot, introdução,
tutorial e primeiro encontro com atributos normais; e uma matriz de 21
checkpoints de QA, cobrindo os dois habitantes de cada bioma e os sete chefes.
Esses JSONs ficam apenas em build/, passam pela validação v15 e são importados
pela interface. Usam Força 36, energia 8 e defesa controlada para repetir
as animações/Ultimates sem alterar o runtime. A matriz é cobertura funcional,
não uma campanha de balanceamento jogada desde o turno inicial.


## Desempenho e cuidados de composição

As telas web reutilizam composições RGB estáticas, com cache limitado.
O fundo é preparado uma vez. Painéis raiz de Loja/Mochila/Altar usam a mesma
composição; painéis sobrepostos e previews mantêm o alpha original.
Molduras com centro totalmente transparente podem desenhar apenas suas
faixas visíveis. Testes comparam os pixels, inclusive a Loja real com hover.

Arquivos comuns do jogador/áudio são reutilizados entre mapa e luta; kits
de outro território, superfícies e o cache de atores são descartados na troca.
A versão Desktop mantém seus renderizadores e carregamento padrão.

O restaurador de snapshot também recupera level/kind/index. Isso é obrigatório
ao reconstruir um motor temporário para confirmar recompensas; assumir nível 1
nessa operação corromperia o avanço da campanha. A conclusão automática de
Zanzara aguarda o commit antes de abrir o epílogo e permite tentar novamente
se a gravação falhar.

A matriz de QA verifica os 14 comuns, os sete chefes, a dupla de duas fases,
as três Ultimates do jogador e os especiais dos chefes. As cartas de intenção
e a pose de derrota da segunda fase da dupla compartilham o mesmo grupo de
recursos, preservando as chaves internas originais.

## Resultado da validação — 25/11/2026

Relatório reproduzível: [validação da Etapa 4](validacao_web_etapa4.json).

- Checkpoint da Etapa 3: `742218f`; alterações da Etapa 4 locais na mesma branch.
- Suíte Python: **860 testes em 86 módulos, zero falhas**, em 187,02 segundos.
- Chromium 159: tutorial e primeiro encontro normais, matriz de 21 encontros,
  três Ultimates, progressão dos sete territórios e epílogo aprovados.
- Gerenciamento: 11 verificações aprovadas, incluindo compra, equipamento,
  comparação/upgrade, tutoriais, configurações e persistência após recarregar.
- Pacote inicial: **6,56 MiB**. Recursos: 2.527 arquivos em 39 grupos e 71 pacotes
  sob demanda, somando **358,72 MiB** comprimidos. Gerenciamento: 72,86 MiB;
  jogador: 32,18 MiB; kits de inimigos: 0,90 a 40,50 MiB; epílogo: 29,62 MiB.
  Esses grupos são baixados ao entrar nos respectivos contextos.
- Abertura do menu nesta execução: **8,80 s**. FPS mediano amostrado em combate:
  **33,90**, com quedas nos efeitos/carregamentos; não representa 60 FPS sustentados.
- Pico observado: heap WASM **723,50 MiB** e heap JS **214,58 MiB**. São medidas
  distintas de heap, não consumo RSS do processo. O pico WASM anterior à limpeza
  dos caches de poses foi 1.217,19 MiB.
- Loja: mediana de 37,95 FPS na verificação de gerenciamento. Uma amostra de perfil
  específica passou de aproximadamente 140 ms para 13 ms de desenho; o teste de
  pixels preserva a composição da Loja real, inclusive durante hover.
- Nenhum arquivo do instalador Windows ou requisito nativo foi alterado.
  Mobile/PWA e entrada por toque permanecem fora desta etapa.

A campanha funcional usa os checkpoints de QA descritos acima; estes resultados
não substituem uma campanha natural de balanceamento nem validação em celulares.

