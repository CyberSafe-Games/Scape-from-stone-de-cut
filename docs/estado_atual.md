# Estado atual do projeto — 24/11/2026

Referência vigente conferida no código. O [contrato JSON](contrato_atual.json)
e o [catálogo LV1/LV2](cartas_e_estados.md) registram valores reais.
Relatórios marcados como históricos não redefinem as regras desta versão.

## Cartas, níveis e ultimates

95 definições: **20 tipos disponíveis e 75 bloqueados** para compra, drops e deck.
Deck de **6–18 cópias**, até três por tipo; rascunho inválido não substitui o
último deck válido. Evolução individual: três materiais do tipo + ouro de
UPGRADE_PRICES, no máximo três upgrades/run. Material custa 15; reserva até nove.

Artes LV1 padrão em assets/cards/; LV2 prateadas em assets/cards/lv2/.
As 40 artes têm dimensões individuais registradas no manifesto; o enquadramento
é proporcional. O manifesto define contorno/centro do losango por arte.
Nível, custo e descrição seguem a cópia real; um único custo dinâmico, sem
badge adicional. Não presumir redução de custo no LV2: usar instance_card.
Artes substituídas ficam fora das pastas ativas no arquivo local ignorado
_arquivos_antigos_para_deletar/, ou são removidas após conferir referências.

Ultimates: cartas douradas ornamentadas completas, molde da Esfera Protetora LV2 (316×489), exterior
transparente, **2 de energia e 20 de carga** para as três. Custo e rodapé dinâmicos.

| ID | Ultimate | Energia | Carga | Efeito |
|---|---|---:|---:|---|
| mana_ancestral | Mana Ancestral | 2 | 20 | Restaura sua energia para 8 e remove todos os seus efeitos negativos. |
| forcas_ancestrais | Forças Ancestrais | 2 | 20 | Ganhe 12 de força ate o fim do combate e 40 de escudo por 2 turnos |
| rugido_da_floresta | Rugido da Floresta | 2 | 20 | Destrua o escudo inimigo, cause 60 de dano e aplique Fraqueza por 3 turnos. |

Mana não compra cartas nem altera energia máxima. Força termina com a luta;
Escudo usa camadas de dois turnos. O dano 60 do Rugido é base e respeita bônus,
Fraqueza/Vulnerável e proteções como Totem; destrói Escudo antes de atacar.
Carga inicia em zero em toda nova batalha, sem herdar carga de outra luta ou
do campo legado carga_ultimate. Retomar o snapshot de uma luta ainda viva
restaura seu estado, incluindo a carga. A passagem da dupla para Tekks é a
mesma luta e conserva o estado/carga do jogador.

## Combate e estados

Energia inicial base 2, teto 8; bônus permanentes podem alterar o início.
Mão inicial 3, limite 5; cartas restantes ficam na mão ao encerrar.
Cemitério: descarte por uma energia, uma troca grátis por turno.

- Veneno: 1–2 stacks/aplicação, teto 5, duração 2 renovada inclusive no teto.
  No fim do turno do afetado causa 5×stacks direto ignorando Escudo, reduz
  duração e zera ao expirar.
- Sangramento: 1–2 stacks, teto 5, duração 2 renovável. Após o primeiro ataque
  de cada turno: 3×stacks direto à vida de quem sangra, mesmo se o golpe for
  absorvido. Uma ativação/turno; multigolpe conta uma ação. O contador reinicia
  no início e a duração decresce no fim sem dano extra.
- Debuffs de impacto só aplicam ou renovam quando o golpe tira vida. Escudo
  que absorva todo o dano impede a aplicação, mesmo quebrando. Ganhar Escudo
  preserva os negativos ativos; efeitos diretos mantêm suas próprias regras.
- Choque: somente inimigos aplicam ao jogador; -1 energia por stack no próximo
  início, mínimo zero; todos os stacks removidos após aplicar. Jozephino: 1 na
  descarga comum, 2 no especial.
- Resetar estados temporários, durações e contadores no início/fim do combate.
  HUD mostra stacks, dano por gatilho e turnos; purificação preserva benefícios.

## Mercado, Altar e Mochila

Mercado Silencioso: cenário/mercador ilustrados, quatro cartas/página, preços
reais, hover e feedback. Cura até **20 HP atual por 30/45/60 ouro**, máximo
**três compras/run**. Vida cheia não cobra nem conta. Não aumenta vida máxima;
melhorias permanentes usam fragmentos entre runs. Preços em CARD_PRICES.

Altar: cenário místico ilustrado, cinco tipos/página, seleção da cópia,
Antes→Depois calculado, LV2 prateado, materiais/preço e confirmação com runas.

Mochila Ancestral: mesa de expedição, couro costurado, deck à esquerda,
reserva de seis tipos/página ao centro, inspeção fixa à direita e aba de
Ultimates. Filtros acompanham a próxima cópia livre, priorizando LV2.
Padding entre carta e moldura externa; carta inteira e custo único.
Hover não captura cliques; transações/rollback continuam no motor.

Intenções: ícones no canto superior direito; uma ação comum e duas de chefe.
Hover com arte mostra somente a própria carta ampliada, x central e y≈43%,
limitada às bordas, acima da arena e sem painel de texto lateral. Sem arte:
ficha textual única. Consulta não altera planos nem sorteios.

## Campanha e saves

Sete territórios, **dois encontros comuns antes de cada chefe**: 14 encontros.
Revanche não dá ouro/cartas/materiais. Recompensas inéditas são idempotentes.
Vida persiste; chefe vencido pela primeira vez recupera 30% da vida máxima.

| Nível | Território | Nome interno | Nome de exibição |
|---:|---|---|---|
| 1 | Stone de Cut | Guardião da Pedra | Octav, o lobisomem |
| 2 | Mata Sombria | Álvaro e Tex | Alvar & Tekks, Rastreadores |
| 3 | Ruínas Ancestrais | Goblin Nerd | Jozephino, o Inventor |
| 4 | Pântano Abissal | Gordofera | Sir Thomas, a Besta Fera |
| 5 | Fortaleza Caída | Corpo Seco | Jan-Pietro, o Imortal |
| 6 | Pico da Vigília | Carrasco da Vigília | Labrro, o Carrasco |
| 7 | Santuário de Pedra | Zanzara | Zanzara, Líder do Clã Moskar |

Saves v14: três slots e laboratório separado, perfil permanente, snapshot de
combate vivo e gravação atômica/revisão. Derrota encerra a run; nova jornada
reinicia recursos temporários mantendo perfil/fragmentos. Epílogo já existe
após Zanzara; laboratório permite revê-lo. Não restaurar o antigo checkpoint
de uma run morta.

## Famílias de animação

| Família | Organização ativa |
|---|---|
| Octav / Jan-Pietro / Labrro | 6 folhas RGBA 4×2 por boss; 8 quadros row-major; célula 448×320 |
| Outros chefes legados | Ações de 12 poses, fontes de idle/dano de 8 |
| Zanzara necromante | Faixas próprias de 8 poses; renderizador/âncoras específicos |
| 14 inimigos comuns | 8 poses/grupo; canvas 448×260 |
| Jaum Manel | Ações/cartas/ultimates de 12; idle/dano de 8 |
| Camadas de Ultimate | Efeitos separados, inclusive sequências de 12; não são o corpo |

Boss1 do ZIP=Octav, Boss5=Jan-Pietro e Boss6=Labrro. Jozephino mantém o ID
goblin nerd, não a folha Boss6 externa. Jan-Pietro: apoio (224,318), botas
idênticas no idle e 160 ms/pose. Jozephino: oito respirações estáveis, botas
fixas, 160 ms/pose (6,25 FPS), ping-pong; sem encolher os intermediários.

Dano inimigo: 560 ms, hold visual ≈90 ms, apoio registrado, recuo apenas
horizontal até 12 px internos e pulso curto. Poses incompatíveis são omitidas;
sem poses válidas, guarda íntegra + recuo/flash. Sem rotação/achatamento,
sem reiniciar a fase do idle; a próxima ação aguarda a reação.
[Auditoria do dano](reacoes_dano.md): 27 formas, incluindo duas fases da dupla.

## Ambiente e verificação

Canvas 1920×1080; janela 1280×720; 60 FPS. Mouse convertido para canvas.
Pygame no runtime; Pillow/NumPy no desenvolvimento. Áudio/trilha ativos por
contexto; IDs e volumes em src/config. IDs de personagens/assets são estáveis.

~~~powershell
python -m pip install -r requirements-dev.txt
python -B devtools/validate_isolated_tests.py --report docs/validacao_auditoria_documentacao.json
python -B devtools/audit_project_docs.py --output docs/auditoria_documentacao.json
~~~

O executor usa unittest, módulos isolados e SDL dummy. Não confundir resultado
incremental com nova suíte integral. Veja [a auditoria por arquivo](auditoria_documentacao_testes.md)
e as convenções completas no [AGENTS.md](../AGENTS.md).

## Integração de 24/11/2026 — instalador, áudio e espólios

As PRs #29 e #30 adicionam build Windows por PyInstaller/Inno Setup e workflow
do GitHub Actions, com dados graváveis em LOCALAPPDATA no executável. No modo
fonte os dados continuam no repositório. Ver [build Windows](build_windows.md).

O altar de espólios pós-combate usa assets/ui/rewards/, seleção de carta nova
ou materiais, preview lateral, confirmação com pulso e pulo mantendo o ouro.
A decisão é aplicada uma única vez, incluindo fechar a janela durante o pulso.
Vitória sobre Zanzara segue para o epílogo sem altar de espólios.

As animações de derrota (Slime, Morcego, Vinimuth e poses dos demais kits)
coexistem com as reações de dano suavizadas. Os novos áudios de debuffs e
contextos musicais da abertura/epílogo são preservados. Lost Time toca a partir
da primeira fala de Octav no epílogo; fonte/licença no
[guia de áudio](../assets/audio/README.md).
