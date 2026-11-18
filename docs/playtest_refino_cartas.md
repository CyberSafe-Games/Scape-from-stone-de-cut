# Playtest da revisão de cartas — 18/11/2026

Branch `feature/refino-cartas-roguelite`, criada da main `0240b5b`, após a integração da PR #24. Esta revisão reúne os ajustes aprovados posteriormente para uma nova avaliação do grupo.

## Regras desta versão

| Carta | Regra atual |
| --- | --- |
| Investida | Custo 2; dano 18/24. Após o ataque, remove 25% do Escudo restante, arredondando para baixo. |
| Disparo de Arco | Sem alteração: custo 2, dano 20/26. |
| Machados Gêmeos | Custo 5; dano 40/50 preservado. |
| Mana Ancestral | Custo 5 e carga 20. Restaura energia para 8 e limpa efeitos negativos, sem comprar cartas. |
| Máscara Ancestral | Custo 4; cura 14/18, Escudo 22/28. |
| Amuleto Dissipador | Remove efeitos positivos, Escudo e Força do inimigo; preserva seus efeitos negativos. |
| Surto de Energia | Mesma mecânica; indica o ganho adicional possível no próximo turno ou “SEM GANHO”. |

Na Investida, 40 de Escudo → ataque LV1 absorve 18 → sobram 22 → remove cinco → restam 17. LV2 deixa 12. Sem Escudo, causa apenas o dano normal; não adiciona dano à vida pela quebra. Totem protege o ataque inteiro, inclusive contra a quebra. As camadas remanescentes de Escudo mantêm suas durações.

A indicação do Surto considera o aumento natural da energia máxima no próximo turno e bônus já pendentes, sob o teto oito. Não prevê futuras ações do inimigo; Choque é aplicado depois do bônus. O custo da carta não foi alterado.

## Executar

Com o jogo fechado, sem alterações locais pendentes, no PowerShell da pasta do projeto:

```powershell
git fetch origin
git switch --track origin/feature/refino-cartas-roguelite
# Se já existir: git switch feature/refino-cartas-roguelite
# Para atualizar esta branch posteriormente: git pull --ff-only
.\.venv\Scripts\python.exe main.py
```

Se ainda não houver ambiente Python, seguir a instalação descrita em `playtest_balanceamento_grupo.md`, substituindo o nome da branch por esta revisão. Preservar os saves anteriores; usar um slot comum novo para comparar dificuldade inicial, fora do Laboratório. Não há executável empacotado nem novas dependências.

## Avaliar

1. Comparar Investida e Arco contra inimigos com e sem Escudo. Conferir se a quebra após o ataque ajuda a preparar as próximas cartas.
2. Experimentar Machados + Mana. A Mana mantém a limpeza, mas não acrescenta cartas à mão; verificar se a combinação continua útil sem dominar as outras escolhas.
3. Comparar a Máscara com cura separada e defesa. Anotar se a redução da cura deixou a sustentação insuficiente.
4. Usar Amuleto após aplicar Veneno, Sangramento, Fogo ou Vulnerabilidade: esses debuffs devem continuar ativos.
5. Conferir Surto no início e no fim de lutas longas. O aviso deve mostrar quando o teto torna o ganho nulo.

Registrar jogador, tentativa, melhorias permanentes, especial, deck/LV2, curas usadas, último inimigo e dúvidas/bugs. Separar a primeira tentativa das seguintes e anotar quando houve dicas.

## Evidência e limites

Suíte completa reexecutada: **664 testes aprovados em 68 módulos**, sem reutilizar resultados; relatório `validacao_pr_refino_cartas.json`. Smoke visual aprovado com saves temporários; testes incluem ordem da quebra, Totem, arredondamento e duração das camadas, preservação dos debuffs, Mana sem compra e indicação do Surto.

Os relatórios de 50, 70 e 100 runs presentes na branch são registros históricos de versões intermediárias. Em particular, os 11% das cem runs usaram Mana sem limpeza e valores anteriores à revisão de Máscara/Amuleto/Investida. **Não representam a taxa desta versão nem uma probabilidade humana.** Nenhuma simulação nova de campanha foi usada para afirmar equilíbrio final desta revisão. A avaliação do grupo continua necessária.

Não fazer merge antes da avaliação e aprovação do grupo.
