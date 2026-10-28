# Laboratório de Testes

Na tela de seleção das três crônicas, clique em **LABORATÓRIO DE TESTES [T]** ou pressione **T**. O jogo abre diretamente o mapa com todos os pontos concluídos e disponíveis para repetição.

O arquivo separado `saves/modo_teste.json` é criado automaticamente no primeiro acesso. Ele não ocupa nenhum dos três espaços normais e não substitui seus arquivos. O laboratório já foi criado neste workspace.

## Recursos

- Vida infinita contra ataques, fogo, veneno e sangramento. A HUD exibe ∞ e um aviso de laboratório.
- Sete territórios concluídos e os 21 encontros comuns liberados para repetir.
- Todas as 20 cartas comuns na coleção da mochila. Equipe até seis tipos, com três cópias por tipo, conforme as regras normais.
- As três ultimates desbloqueadas e 9.999 moedas iniciais.
- O deck equipado, a ultimate escolhida e as moedas são salvos normalmente. Os desbloqueios são mantidos ao reabrir o laboratório, incluindo cartas futuras adicionadas ao catálogo.

A imunidade não remove efeitos nem preserva Escudo artificialmente: dano consome Escudo, Totem e durações normalmente, mas não reduz os pontos de vida. Energia, compras de cartas, dano causado e carga de ultimate continuam seguindo as regras normais para permitir testes do combate real.

## Reconhecimento e isolamento

O jogo só ativa a imunidade se o identificador do arquivo for `modo_teste` e o campo superior `modo_teste` for `true`. Alterar apenas o nome exibido de uma crônica não ativa o modo. Carregar uma crônica normal desativa a imunidade. Os três saves normais e sua progressão permanecem separados.
