# Scape From Stone de Cut

> Referência vigente — auditoria de 23/11/2026. [Estado atual](docs/estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

**A floresta resiste. Escreva sua estratégia. Defenda sua terra.**

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.x-e34c26)
![Plataforma](https://img.shields.io/badge/Plataforma-PC-1f6feb)

## Sobre o jogo

*Scape From Stone de Cut* é um jogo de **estratégia, roguelike, RPG de turno e deckbuilding** para PC, com classificação indicativa a partir de 10 anos.

Foi criado para a disciplina de Programação Para Jogos na universidade, com o objetivo de aplicar, na prática, os conceitos fundamentais do desenvolvimento de jogos usando Python e Pygame: ciclo principal, cenas, estados, entrada, interface, saves e build. A proposta de design é simples de explicar e difícil de dominar: **pouca ação por turno, muita consequência por escolha**.

## História

Jaum Manel, jovem indígena da aldeia Stone The Cut, vê sua terra invadida pelo Clã Moskar e sua tribo capturada por Zanzara, Líder do Clã Moskar. Sozinho e sem exército, ele atravessa o próprio território ocupado, vence combates por turnos, monta seu baralho carta a carta e marcha rumo ao Santuário de Pedra para libertar seu povo.

## Direção visual e guias atuais

Mercado Silencioso, Altar de Aprimoramento e Mochila Ancestral usam ambientações
ilustradas, molduras ornamentadas, cartas completas e custo dinâmico.
[Loja/Altar](docs/loja_altar_visual.md) · [Mochila](docs/mochila_visual.md) ·
[Artes LV1/LV2](docs/cartas_packs_lv1_lv2.md) · [Animações](docs/reacoes_dano.md).

Regras canônicas e inventário:
[estado atual](docs/estado_atual.md) · [auditoria](docs/auditoria_documentacao_testes.md).

## HUD e guias de gerenciamento

O botão **MENU** fica no centro superior do combate, entre duas barras de vida
simétricas. O preenchimento de HP usa toda a abertura interna da moldura,
com recorte para preservar as águias; HP parcial reduz a largura proporcionalmente.
O nome da arena fica acima, sem ocupar os retratos e os status.
As molduras externas compartilham ouro envelhecido/pedra; cantos ornamentados
são preservados ao redimensionar. Cartas LV1, LV2 prateadas e Ultimates douradas
mantêm suas identidades e o custo dinâmico único.

Na primeira visita ao **Mercado Silencioso**, à **Mochila** e ao **Altar de
Aprimoramento**, um guia ancestral destaca os controles reais em passos curtos.
Use **Próximo**, **Anterior** e **Concluir**, ou feche pelo ×/Esc. O botão
**? AJUDA** permite rever cada guia. A conclusão/dispensa é salva por tela no
perfil do slot, preservada entre runs. Saves anteriores migram para v15 sem
perder cartas, ouro, progresso ou snapshots. Falha ao gravar mantém o guia
aberto para nova tentativa; Esc nessa situação sai sem registrar a conclusão.

## Configurações e retratos

O **Santuário dos Ajustes** usa cenário ilustrado de pedra ancestral,
pergaminho escuro, runas e ouro envelhecido. As abas Áudio, Vídeo, Jogo e
Controles preservam as preferências existentes. Sliders e seletores têm
textura e destaque rúnico; alterações continuam aplicadas e salvas na hora.
No combate, abra **MENU → OPÇÕES**. **Retornar ao Combate** fecha as camadas
de pausa sem reiniciar a luta; Esc volta somente uma camada.

Na aba **Jogo**, **Rever Tutoriais** abre uma biblioteca de consulta de Loja,
Mochila e Altar, sem marcar guias como vistos ou modificar o slot. **Sair para
o Menu** pede confirmação e salva o progresso válido; falha de gravação cancela
a saída, e recompensas/transições pendentes precisam ser concluídas primeiro.

Os 14 inimigos comuns usam a mesma moldura e proporção do protagonista na HUD.
Faces fornecidas são preservadas; Slime e Macaco têm retratos dedicados.
Os 14 retratos dos biomas, mais Goblin e Guarda Sombrio do gerador legado,
usam recortes individuais e escala interna proporcional em
contain, com margem para preservar rosto, orelhas, cristas e focinho.

## Como jogar

**Controles por mouse e atalhos**

| Ação | Comando |
|---|---|
| Selecionar cartas, botões e menus | Botão esquerdo |
| Voltar / cancelar | `Esc` |
| Jogar no menu principal | `Enter` ou `Espaço` |
| Cemitério | `C` |
| Tela cheia / janela | `F11` |
| Maior janela 16:9 / janela 1280×720 | `F10` |
| Preparar nova jornada após derrota | `R` |
| Laboratório de testes (na seleção de saves) | `T` |

**Um combate, em resumo:**

1. No seu turno, a energia é restaurada e a mão é completada; você joga cartas gastando energia. A mão vai de 3 a até 5 cartas ao longo do combate (a energia máxima também cresce, de 2 até 8).
2. A HUD mostra a ordem das ações planejadas do inimigo. Passe o mouse sobre um ícone de intenção para ampliar a carta quando a arte completa estiver disponível.
3. Ao encerrar o turno, as cartas que sobraram ficam na mão e o inimigo age. O Escudo absorve o dano de ataques antes que eles atinjam a vida.
4. Após vencer um encontro pela primeira vez, o altar de espólios mostra o ouro conquistado. Selecione uma carta nova ou abra **Escolher materiais** para ver as cópias e a reserva de cada tipo. Use **Confirmar escolha** para receber a seleção ou **Pular recompensa** para seguir com o ouro da vitória. Revanches não concedem espólios.
5. Se a vida de Jaum Manel zerar, a run termina. Perfil/fragmentos persistem; prepare uma nova jornada. Uma luta viva pode ser retomada por snapshot.

## Principais mecânicas

- **Baralho com três pilhas:** compra, mão e descarte. Se a pilha de compra esvazia, o descarte é reembaralhado.
- **Cartas:** 20 tipos disponíveis com artes LV1 padrão/LV2 prateadas, custo dinâmico único e evolução individual no Altar. As 75 cartas em desenvolvimento ficam indisponíveis para recompensas, compras e montagem do deck.
- **Altar de espólios:** cenário ilustrado em `assets/ui/rewards/`, com brasas ascendentes, runas ao apontar para uma oferta e pulso dourado na confirmação. A prévia lateral usa a arte e o custo atuais das cartas, incluindo a moldura prateada em LV2. Para abrir o piloto com um save temporário, execute `testar_polimento_audio.bat recompensa` e pressione Espaço para vencer o encontro.
- **Cemitério:** descarte uma carta da mão por 1 de energia, ou faça 1 troca grátis por turno com uma carta do descarte.
- **Ultimates:** a carga começa em **0/20** em toda batalha e sobe conforme a energia gasta em cartas. Ao atingir 20, você pode ativar a Ultimate equipada: **Mana Ancestral**, **Forças Ancestrais** ou **Rugido da Floresta**. A escolha equipada é salva. A carga vale somente para a batalha atual. Todas custam **2 de energia**. Mana restaura a energia para 8 e remove negativos; Forças concede +12 de Força até o fim do combate e 40 de Escudo por 2 turnos; Rugido destrói o Escudo inimigo, causa 60 de dano base e aplica Fraqueza por 3 turnos.
- **Mercado Silencioso:** compre tipos de cartas ou cure até 20 HP atual por 30/45/60 ouro, até três compras/run. Vida cheia não cobra. Melhorias permanentes ficam entre runs.
- **Mochila Ancestral:** deck de 6–18 cartas, três cópias por tipo, reserva paginada/filtros, inspeção fixa e aba de Ultimates. Rascunho inválido preserva o último deck salvo.
- **Tutorial guiado:** primeiro acesso a um save ensina as regras com balões e textos na tela.
- **Saves v15 em 3 slots** e **Laboratório de Testes** via `T`. Os saves registram progresso, coleção, moedas e Ultimates desbloqueadas e equipada.
- **Vida entre lutas:** a vida atual é mantida entre combates. A vitória sobre um chefe de território recupera 30% da vida máxima, respeitando o limite.

### Efeitos negativos

- **Veneno:** cada aplicação adiciona 1 ou 2 stacks, até 5, e renova a duração para 2 turnos. No fim do turno da entidade afetada, causa `5 × stacks` de dano direto, ignorando Escudo, e perde 1 turno de duração.
- **Sangramento:** cada aplicação adiciona 1 ou 2 stacks, até 5, e renova a duração para 2 turnos. O primeiro ataque de cada turno causa `3 × stacks` de dano direto à vida de quem está sangrando. A duração diminui no fim do turno da entidade afetada.
- **Debuffs de impacto:** o golpe precisa tirar vida para aplicar ou renovar o debuff. Um Escudo que absorve todo o dano impede a aplicação, mesmo quando quebra. Ganhar Escudo preserva os debuffs já ativos.
- **Choque:** só inimigos aplicam. Cada stack reduz a energia inicial do próximo turno do jogador em 1, até o mínimo de 0. Todos os stacks expiram assim que a redução é aplicada.

## Progressão

O jogo tem uma campanha linear de **sete territórios**. Em cada um, há 2 combates comuns antes do chefe; concluir o chefe desbloqueia o próximo território.

| # | Território | Chefe |
|---|---|---|
| 1 | Stone de Cut | Octav, o lobisomem |
| 2 | Mata Sombria | Alvar & Tekks, Rastreadores |
| 3 | Ruínas Ancestrais | Jozephino, o Inventor |
| 4 | Pântano Abissal | Sir Thomas, a Besta Fera |
| 5 | Fortaleza Caída | Jan-Pietro, o Imortal |
| 6 | Pico da Vigília | Labrro, o Carrasco |
| 7 | Santuário de Pedra | Zanzara, Líder do Clã Moskar (chefe final) |

## Instalação e execução

### Windows

#### Instalar com o assistente

1. Abra a página de [Releases do jogo](https://github.com/CyberSafe-Games/Scape-from-stone-de-cut/releases/latest).
2. Em **Assets**, baixe `ScapeFromStoneDeCut-Setup-x.y.z.exe` (use a versão mais recente disponível).
3. Abra o arquivo baixado e siga o assistente. A instalação é por usuário, não pede Python ou Pygame e, por padrão, não exige permissão de administrador. O atalho do Menu Iniciar é criado automaticamente; o atalho da Área de Trabalho é opcional.
4. Ao terminar, abra **Scape From Stone de Cut** pelo Menu Iniciar.

O Windows SmartScreen ou um antivírus pode avisar sobre um instalador sem assinatura digital. Se baixou o arquivo da página oficial de Releases e deseja prosseguir, no aviso do SmartScreen selecione **Mais informações → Executar assim mesmo**. Não execute instaladores de outras origens.

#### Usar a versão portátil

Na mesma página de Releases, baixe `ScapeFromStoneDeCut-portable-x.y.z.zip` em **Assets**. Use **Extrair Tudo** do Windows e execute `ScapeFromStoneDeCut/ScapeFromStoneDeCut.exe` dentro da pasta extraída. Extraia a pasta inteira e mantenha os arquivos juntos; não execute o jogo de dentro do ZIP.

Saves e configurações ficam em `%LOCALAPPDATA%\ScapeFromStoneDeCut`. Desinstalar pelo Windows preserva esses dados por padrão e oferece a opção de apagá-los. Consulte também [o guia de instalação para Windows](docs/build_windows.md).

### Executar pelo código-fonte

Pré-requisitos: **Python 3.12 ou mais recente**. As dependências vêm do `requirements.txt` (somente Pygame).

```bash
git clone https://github.com/CyberSafe-Games/Scape-from-stone-de-cut.git
cd Scape-from-stone-de-cut

# Em Linux/macOS, o launcher pode ser `python3` em vez de `python`
python3 -m pip install -r requirements.txt
python3 main.py
```

O jogo abre em uma janela de 1280×720 com renderização interna de 1920×1080. Use `F11` para alternar tela cheia e `F10` para escolher um tamanho de janela maior ou o padrão.

## Testes

A suíte usa `unittest` (não pytest). Como há muitos assets, os testes headless pedem os drivers dummy do SDL:

```bash
python3 -m pip install -r requirements-dev.txt

# Suíte completa em processos isolados (configura SDL dummy e libera caches)
python3 -B devtools/validate_isolated_tests.py --report docs/validacao_auditoria_documentacao.json

# Auditoria de Markdown, links e inventário de testes
python3 -B devtools/audit_project_docs.py --output docs/auditoria_documentacao.json

# Um módulo específico
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest tests.test_tactical_cards -v
```

Existe um laboratório de testes dentro do jogo: na tela de seleção de saves, pressione `T` para abrir o Laboratório de Testes (vida infinita e tudo desbloqueado).

## Estrutura do projeto

```text
main.py                 # Ponto de entrada do jogo
src/config/             # Resolução, FPS, caminhos, paleta, layout, nomes de exibição e trilha
src/core/               # Janela, gerenciador de cenas, assets, áudio
src/scenes/             # Menu, seleção de saves, tutorial, mapa, batalha, mochila, loja, configurações e modais
src/systems/            # Regras de jogo sem interface: combate, saves, campanha, cartas, inimigos, loja
src/models/             # Entidades (jogador, inimigos, cartas, efeitos, ultimates)
src/ui/                 # HUD, cartas, sprites animados e helpers de desenho
assets/                 # Sprites, efeitos e áudio
assets/cards/           # LV1 e manifesto geométrico
assets/cards/lv2/       # Artes LV2 prateadas
assets/ultimates/       # Cartas douradas
assets/ui/              # Mercado, Altar e Mochila ilustrados
assets/bosses/sheets_eight/ # Folhas 4x2 de Octav/Jan-Pietro/Labrro
assets/intent_art/      # Arte das intenções de chefes e inimigos
docs/                   # Documentos e prévias de arte/animação
devtools/               # Scripts de preparo/preview de sprites (uso interno)
tests/                  # Suíte de testes (unittest)
saves/                  # Saves locais dos jogadores (ignorado pelo git)
```

## Estado atual e roadmap

**Em funcionamento hoje:** campanha de sete territórios, combate por turnos, tutorial guiado, cutscenes de introdução, pós-tutorial e epílogo, diálogos de chefes, menu de configurações, efeitos sonoros e trilha por contexto. As intenções com arte completa exibem a carta inteira em um preview ampliado no centro da arena, acima da mão do jogador.

**Em desenvolvimento:** polimento visual e balanceamento de cartas e encontros.

**Cronograma da equipe (2026):** sprints semanais de 23/09 a 24/11; apresentação parcial em 28/10 e final em 25/11.

## Equipe CyberGames

Projeto acadêmico da disciplina de Programação Para Jogos — Barbacena, 2026.
Orientação do professor Rodrigo Fernandes dos Santos.

- Gabriel Augusto — mecânicas
- João Pedro de Almeida Melo — mecânicas
- Otávio Henrique Nézio Melo — mecânicas
- José Gabriel Mazoni Val — testes das versões
- João Emanuel de Faria — cartas e história
- Lucas Evaristo Almeida de Paula — inimigos
- Marcus Tadeu de Oliveira Souza — som

As decisões de escopo, identidade visual e mecânicas são tomadas e avaliadas pela equipe; a IA é apoio de produção, não autora do design.

## Uso de Inteligência Artificial

A IA foi usada como ferramenta de apoio na criação e aceleração dos sprites e no desenvolvimento de algumas mecânicas, com direção e revisão humana. Todas as decisões de escopo, identidade visual e mecânicas são responsabilidade da equipe; os sprites gerados por IA seguem paleta e referências aprovadas.

## Licença

<!-- TODO: definir licença -->

## Prova web — Etapa 1

Menu e combate contra Slime em Pygbag, sem saves e sem campanha web.
O desktop e o instalador continuam independentes. Consulte
[escopo e execução da prova](docs/web_poc.md).

A Etapa 2 isola serviços desktop/web, saída, viewport e foco; também otimiza
caches de renderização preservando o desktop. Consulte o
[contrato de plataformas](docs/web_platforms.md).

A Etapa 3 adiciona persistência híbrida v15: IndexedDB para slots/perfil/run,
localStorage para preferências, confirmação assíncrona com rollback,
controle de revisão entre abas, checkpoints e exportação/importação JSON.
O piloto --poc inclui as telas reais de gerenciamento e o encontro Slime;
o piloto anterior sem saves continua em `?render=1`.
Veja [persistência web e validação](docs/web_storage.md).

A Etapa 4 integra a campanha Web PC com recursos por contexto, cenas nativas e entrada unificada. Consulte [campanha web](docs/web_campaign.md). O build padrão é completo; use --poc para reproduzir a prova anterior.

A Etapa 5 adiciona controles compactos, inspeção por toque e orientação paisagem no host web. Veja [layout e entrada mobile](docs/web_mobile.md). Desktop e Web PC amplo mantêm o layout anterior.
Validação da Etapa 5: 889 testes Python aprovados, 22 verificações mobile e 11 Web PC. Veja o [relatório completo](docs/validacao_web_etapa5.json).
