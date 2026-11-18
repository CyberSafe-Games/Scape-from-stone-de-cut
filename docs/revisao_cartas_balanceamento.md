# Revisão das 20 cartas disponíveis — 18/11/2026

> Implementação posterior autorizada: Investida 20/26 por duas energias; Máscara cura 14/18 com Escudo 22/28; Amuleto preserva debuffs ao remover benefícios; Surto sinaliza ganho aproveitável ou nulo. As descrições abaixo registram o diagnóstico anterior. 123 testes reexecutados em dez módulos aprovados, consolidado incremental 661/68; smoke de interface aprovado. Alterações locais, sem atualizar PR #24. O valor de Investida cria paridade com Arco, não uma identidade mecânica nova.

Análise da versão local: Machados custa cinco; Mana restaura energia e limpa efeitos, sem comprar cartas. Não houve mudança de regras nesta revisão. As 75 cartas bloqueadas estão fora do escopo.

Fontes: `card_definitions.py`, `roguelite.py`, `tactical_card_effect.py` e `entity.py`. Valores sem bônus de Força/Aura, vulnerabilidade, defesa ou resistências situacionais. Eficiência por energia não substitui disponibilidade na mão, preço em ouro ou oportunidade de uso.

| Carta | Energia | LV1 → LV2 |
| --- | --- | --- |
| Soco Simples | 1 | Dano 6 → 9 |
| Esfera Protetora | 1 | Escudo 10 → 14, duas rodadas |
| Investida | 2 | Dano 18 → 24 |
| Disparo de Arco | 2 | Dano 20 → 26 |
| Lança Perfurante | 3 | Dano 30 → 38 |
| Machados Gêmeos | 5 | Dano 40 → 50 |
| Aura Rubra | 2 | Bônus de ataque 6 → 8, três turnos; reaplicar renova |
| Poção Fragilizante | 1 | Vulnerabilidade +25% por três turnos; LV2 acrescenta cinco de Escudo |
| Poção Purificadora | 1 | Limpa efeitos negativos; LV2 acrescenta seis de cura |
| Totem Protetor | 3 | Ignora um ataque inteiro; LV2 acrescenta oito de Escudo |
| Zarabatana Venenosa | 3 | Dano total 10 → 16 e dois acúmulos de Veneno, duas rodadas |
| Poção Venenosa | 2 | Dois acúmulos de Veneno, duas rodadas; LV2 acrescenta seis de Escudo |
| Adaga Sangrenta | 2 | Dano 8 → 14 e dois acúmulos de Sangramento, duas rodadas |
| Bola de Fogo | 2 | Dano 12 → 18 e uma intensidade de Fogo, três turnos |
| Esfera Escudo | 3 | Escudo 32 → 42, duas rodadas |
| Machado Quebra-Escudo | 1 | Remove Escudo inimigo; LV2 acrescenta oito de Escudo ao usuário |
| Amuleto Dissipador | 2 | Remove todos os efeitos do inimigo, incluindo os negativos, Escudo e Força; LV2 acrescenta oito de Escudo ao usuário |
| Poção de Cura | 3 | Cura 20 → 26 |
| Máscara Ancestral | 4 | Cura/Escudo 18/22 → 24/28 |
| Surto de Energia | 1 | Energia no próximo turno 2 → 3; teto oito |

## Pontos que merecem decisão

1. **Investida e Arco:** mesmo custo, ambos dano simples, mas Investida causa menos nos dois níveis. Arco tem vantagem direta em combate. O preço de aquisição da Investida é menor (40 contra 55), mas isso não cria identidade após obter as duas. Proposta mínima para comparar: Investida 20/26, mantendo custo dois; seria paridade, ainda sem identidade própria. Outra possibilidade depende de decisão humana sobre um efeito secundário. Não alterar ambas automaticamente.

2. **Máscara Ancestral e cura:** por quatro de energia, Máscara combina 18 de cura e 22 de Escudo; por três, a Poção cura 20. No LV2, a diferença de cura segue em apenas dois, com 28 de Escudo adicional na Máscara. Cura e Escudo não são equivalentes nem sempre aproveitados, mas a combinação merece atenção. O plano com Máscara venceu 7/10 na amostra de cem runs, sob a Mana anterior sem limpeza; não isola o efeito da carta. Primeiro candidato de redução para comparação: cura 14/18, mantendo Escudo 22/28 e custo quatro. Evitar enfraquecer simultaneamente toda a defesa, pois as vitórias do bot já se concentram em sustentação.

3. **Surto de Energia:** ao atingir oito de energia máxima, o próximo turno já restaura oito. O bônus é cortado pelo teto, portanto a carta pode gastar energia agora sem produzir energia adicional depois. Isso está de acordo com a descrição e com o limite, mas perde função tarde na luta. Prioridade: explicar na interface quanto poderá ser aproveitado ou sinalizar o bônus nulo. Fazer a carta recuperar energia imediatamente seria uma mudança de mecânica, não uma simples correção numérica.

4. **Amuleto Dissipador:** remove também o Veneno, Sangramento, Fogo e Vulnerabilidade colocados pelo jogador. É comportamento explicitamente descrito, não um bug, mas prejudica os decks de efeitos e pode surpreender. Proposta para avaliação: remover somente efeitos positivos e Escudo/Força do inimigo, preservando debuffs. Exige definir e testar o conjunto removido; não basta trocar a descrição.

5. **Evoluções que mudam de função:** Purificadora LV2 passa a curar; Venenosa LV2 passa a defender; Fragilizante LV2 ganha Escudo. São efeitos implementados e descritos, mas a evolução favorece sustentação em vez de aprofundar a identidade original. Decidir se isso é desejado antes de trocar valores. Não aumentar os acúmulos globais de Veneno/Sangramento: essas regras foram finalizadas separadamente.

6. **Machados e curva de dano:** o novo custo cinco impede dois Machados com apenas oito de energia, mas reduz sua eficiência: LV1 8 de dano/energia, contra 10 do Arco; LV2 10 contra 13. Concentra dano numa carta, mas não é automaticamente o melhor gasto. Preservar a decisão recente durante a avaliação, sem voltar a aumentar seu custo com base somente no antigo combo com compra de cartas.

## O que não é falha comprovada

Poção Venenosa tem pouco dano imediato, mas seu Veneno ignora Escudo; Adaga depende de ações ofensivas que tirem vida; Bola de Fogo causa dano ao longo de turnos e seu Fogo encontra Escudo primeiro. Comparar só o número impresso de dano favorece indevidamente cartas de ataque direto. Totem protege apenas um ataque completo, importante contra golpes fortes, mas chefes com duas ações podem consumir a proteção na primeira.

Esfera Protetora, Esfera Escudo e Soco têm papéis básicos compreensíveis. Lança concentra dano sem exigir tantas cartas na mão. Aura e Fragilizante amplificam sequências de ataques; avaliar com a composição completa. Nesta leitura não foi demonstrado erro novo de implementação nessas cartas. Não atribuir as derrotas dos decks de efeitos exclusivamente aos valores sem comparar políticas de jogo e aquisição.

## Ordem sugerida

Primeiro sinalizar o desperdício do Surto e decidir a função do Amuleto; depois comparar Investida e Máscara isoladamente, nas mesmas sementes e composições. Preservar a nova Mana e o Machado durante essas comparações para não misturar causas. Esta é uma proposta para avaliação, sem implementação e sem atualização da PR.
