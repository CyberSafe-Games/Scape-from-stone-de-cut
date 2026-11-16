# Scape From Stone de Cut

**A floresta resiste. Escreva sua estratégia. Defenda sua terra.**

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.x-e34c26)
![Plataforma](https://img.shields.io/badge/Plataforma-PC-1f6feb)

## Sobre o jogo

*Scape From Stone de Cut* é um jogo de **estratégia, roguelike, RPG de turno e deckbuilding** para PC, com classificação indicativa a partir de 10 anos.

Foi criado para a disciplina de Programação Para Jogos na universidade, com o objetivo de aplicar, na prática, os conceitos fundamentais do desenvolvimento de jogos usando Python e Pygame: ciclo principal, cenas, estados, entrada, interface, saves e build. A proposta de design é simples de explicar e difícil de dominar: **pouca ação por turno, muita consequência por escolha**.

## História

Jaum Manel, jovem indígena da aldeia Stone The Cut, vê sua terra invadida pelo Clã Moskar e sua tribo capturada por Zanzara, Líder do Clã Moskar. Sozinho e sem exército, ele atravessa o próprio território ocupado, vence combates por turnos, monta seu baralho carta a carta e marcha rumo ao Santuário de Pedra para libertar seu povo.

## Capturas de tela

| | |
|---|---|
| ![Jaum Manel em combate](docs/protagonista_doze_frames.png) | ![Chefes do Clã Moskar em batalha](docs/bestiario_em_batalha.png) |
| ![Mochila e baralho](docs/mochila_deck_v2.png) | ![Zanzara, Líder do Clã Moskar](docs/zanzara_batalha.png) |

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
| Reiniciar após a derrota | `R` |
| Laboratório de testes (na seleção de saves) | `T` |

**Um combate, em resumo:**

1. No seu turno, a energia é restaurada e a mão é completada; você joga cartas gastando energia. A mão vai de 3 a até 5 cartas ao longo do combate (a energia máxima também cresce, de 2 até 8).
2. A HUD mostra a ordem das ações planejadas do inimigo. Passe o mouse sobre um ícone de intenção para ampliar a carta quando a arte completa estiver disponível.
3. Ao encerrar o turno, as cartas que sobraram ficam na mão e o inimigo age. O Escudo absorve o dano de ataques antes que eles atinjam a vida.
4. Após vencer pela primeira vez um encontro com recompensa disponível, escolha uma das cartas que você ainda não possui ou pule a escolha. Revanches não dão cartas.
5. Se a vida de Jaum Manel zerar, a run volta ao último checkpoint (tecla `R`).

## Principais mecânicas

- **Baralho com três pilhas:** compra, mão e descarte. Se a pilha de compra esvazia, o descarte é reembaralhado.
- **Cartas:** 20 cartas jogáveis com artes e animações próprias. As 75 cartas em desenvolvimento ficam indisponíveis para recompensas, compras e montagem do deck.
- **Cemitério:** descarte uma carta da mão por 1 de energia, ou faça 1 troca grátis por turno com uma carta do descarte.
- **Ultimates:** a carga começa em **0/20** em toda batalha e sobe conforme a energia gasta em cartas. Ao atingir 20, você pode ativar a Ultimate equipada: **Mana Ancestral**, **Forças Ancestrais** ou **Rugido da Floresta**. A escolha equipada é salva. A carga vale somente para a batalha atual.
- **Mercado Silencioso:** compre cartas ou aumente a vida máxima em 15 por 50 moedas, até 3 vezes por run.
- **Mochila:** monte seu deck em espaços individuais (até 18, com no máximo 3 cópias da mesma carta) e escolha a Ultimate equipada.
- **Tutorial guiado:** primeiro acesso a um save ensina as regras com balões e textos na tela.
- **Saves em 3 slots** e **Laboratório de Testes** via `T`. Os saves registram progresso, coleção, moedas e Ultimates desbloqueadas e equipada.
- **Vida entre lutas:** a vida atual é mantida entre combates. A vitória sobre um chefe de território recupera 30% da vida máxima, respeitando o limite.

### Efeitos negativos

- **Veneno:** cada aplicação adiciona 1 ou 2 stacks, até 5, e renova a duração para 2 turnos. No fim do turno da entidade afetada, causa `5 × stacks` de dano direto, ignorando Escudo, e perde 1 turno de duração.
- **Sangramento:** cada aplicação adiciona 1 ou 2 stacks, até 5, e renova a duração para 2 turnos. Causa `3 × stacks` de dano direto após uma ação ofensiva que tire vida do alvo, até duas vezes por turno. A duração diminui no fim do turno da entidade afetada.
- **Choque:** só inimigos aplicam. Cada stack reduz a energia inicial do próximo turno do jogador em 1, até o mínimo de 0. Todos os stacks expiram assim que a redução é aplicada.

## Progressão

O jogo tem uma campanha linear de **sete territórios**. Em cada um, há 2 combates comuns antes do chefe; concluir o chefe desbloqueia o próximo território.

| # | Território | Chefe |
|---|---|---|
| 1 | Pedra do Corte | Octav, o lobisomem |
| 2 | Mata Sombria | Alvar & Tekks, Rastreadores |
| 3 | Ruínas Ancestrais | Jozephino, o Inventor |
| 4 | Pântano Abissal | Sir Thomas, a Besta Fera |
| 5 | Fortaleza Caída | Jan-Pietro, o Imortal |
| 6 | Pico da Vigília | Labrro, o Carrasco |
| 7 | Santuário de Pedra | Zanzara, Líder do Clã Moskar (chefe final) |

## Instalação e execução

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

# Suíte completa (pesada, pode passar de 5 minutos)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest discover -s tests -t .

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
assets/cards/           # Cartas jogáveis
assets/intent_art/      # Arte das intenções de chefes e inimigos
docs/                   # Documentos e prévias de arte/animação
devtools/               # Scripts de preparo/preview de sprites (uso interno)
tests/                  # Suíte de testes (unittest)
saves/                  # Saves locais dos jogadores (ignorado pelo git)
```

## Estado atual e roadmap

**Em funcionamento hoje:** campanha de sete territórios, combate por turnos, tutorial guiado, cutscenes de introdução e pós-tutorial, diálogos de chefes, menu de configurações, efeitos sonoros e trilha por contexto. As intenções com arte completa exibem a carta inteira em um preview ampliado no centro da arena, acima da mão do jogador.

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
