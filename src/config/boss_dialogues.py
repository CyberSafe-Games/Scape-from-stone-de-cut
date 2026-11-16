"""Falas antes dos confrontos com chefes.

Edite apenas as listas de falas. Cada fala é um par (personagem, texto).
Use 'Jaum Manel' ou o nome exato do inimigo. Deixe () para não exibir diálogo.
"""

BOSS_DIALOGUES = {
    "guardião da pedra": (
        ("guardião da pedra", "Parece que uma das presas conseguiu sair do cativeiro..."),
        ("Jaum Manel", "Para vocês meu povo não passa de presas? Vocês vao pagar pelo que fizeram com nossas terras!"),
        ("guardião da pedra", "Uma caça sem uma luta não tem adrenalina alguma! \n Me mostre o que você sabe fazer, indiozinho!"),
    ),
    "álvaro e tex": (
        ("Jaum Manel", "Você é humano, porque ataca nossa tribo? Nós nunca fizemos mal a vocês! \n Muito menos aos goblins!"),
        ("alvaro e tex", "O clã Moskar nos ofereceu abrigo quando precisávamos de ajuda, devemos nossa lealdade a eles!"),
        ("alvaro e tex", "Meu amigo Tekks Não é um goblin! \n Nossa cidade foi contaminada com uma bactéria que deixou sua pele verde!"),
        ("Jaum Manel", "Mentiroso! \n Se isso é verdade, porque só um de vocês é verde?"),
        ("alvaro e tex", "Digamos que meu parceiro nunca foi muito fã de banhos... \n Agora chega de conversa, esta terra vai ser o nosso novo lar, prepare-se!"),

    ),
    "goblin nerd": (
        ("Jaum Manel", "Deixa eu adivinhar, você não é um goblin, só ficou verde porque não toma banho certo?"),
        ("goblin nerd", "Como você ousa! \n Sou um goblin desde o nascimento."),
        ("Jaum Manel", "Ah! Peço desculpas, mas porque você está atacando nossa tribo? \n Protegemos a floresta assim como seu povo."),
        ("goblin nerd", "Proteger a floresta? essas terras não passam de um depósito de matéria prima para as minhas invenções!"),
        ("Jaum Manel", "Desde quando os goblins exploram as terras da floresta? \n Não faz sentido, essas terras são tudo o que nós temos!"),
        ("goblin nerd", "QUANTA HIPOCRISIA! \n Foi o seu povo que destruiu a minha terra natal, e agora só estou retribuindo o favor!"),
        ("goblin nerd", "Porém tudo em nome da ciência, claro Mwhahahahahaha!!"),
        ("Jaum Manel", "Não consigo acreditar.") 
        ),
    "gordofera": (
        ("Jaum Manel", "Outro tipo de monstro? \n como vocês acabaram assim?"),
        ("gordofera", "Monstro? Prefiro que me chame de Tom, ou melhor, Sir Thomas para você, rapazinho!"),
        ("Jaum Manel", "Sir Thomas? \n Desde quando um monstro tem nome e sobrenome?"),
        ("gordofera", "Sabe garoto, nem todos nós somos monstros aqui, eu por exemplo, sempre fui um renomado conde do reino de onde eu vim!"),
        ("gordofera", "Ou melhor, eu era um renomado conde do reino de onde eu vim, antes de adoecer...!"),
        ("Jaum Manel", "Não entendo, que tipo de doença é essa que te transformou em um monstro?"),
        ("gordofera", "Já basta! \n Não devo explicar minha história a um simplório insolente feito você! \n Irei lhe ensinar alguns modos!"), 
        ),
    "corpo seco": (
        ("Jaum Manel", "Eu lembro de você, durante o ataque a nossa tribo, você era um esqueleto por completo! \n Como seu rosto voltou ao normal?"),
        ("corpo seco", "Sabe garoto, como você conseguiu chegar tão longe, irei lhe dizer um pouco de nossa história. \n Nenhum de nós é o que parece ser, essa é a habilidade de nosso líder, o grande zanzara!"),
        ("Jaum Manel", "Habilidade? Zanzara? \n O que você quer dizer com isso?"),
        ("corpo seco", "Zanzara é o líder de nosso clã Moskar, seu poder é tão grande que ele permite nos curarmos de todas as nossas doenças, e aumentar a nossa longevidade..."),
        ("Jaum Manel", "Então vocês são imortais? \n E o que minha tribo tem a ver com isso?"),
        ("corpo seco", "Todo poder tem um preço, quanto mais o tempo passa, nosso corpo não consegue aguentar, e vamos nos tornando outra coisa. \n É questão de tempo até que todos nós nos tornemos monstros por completo."),
        ("corpo seco", "De tempos em tempos, precisamos invadir outros povos, e roubar a sua longevidade, para voltarmos à nossa forma original."),
        ("Jaum Manel", "Como pode!! \n Quantos outros povos vocês já atacaram? \n Quantas terras vocês já devastaram em busca dessa tal imortalidade?"),
        ("corpo seco", "Para ser sincero garoto, não consigo me lembrar... \n Nesses meus 300 anos de servidão a zanzara, já perdi a conta de quantas tribos já destruímos..."),
        ("corpo seco", "No ínicio eramos como uma família, mas com o passar do tempo, a ganância tomou conta de todos nós, e nos tornamos monstros, tanto em aparência quanto em caráter..."),
        ("corpo seco", "Não concordo com Zanzara, mas não vou me opor a ele, então garoto, se por um acaso você conseguir derrota-lo, por favor, de um fim a essa maldição. \n Meus companheiros não merecem viver assim, eles não sabem o preço desse poder"),
        ("Jaum Manel", "Não posso deixar que isso continue acontecendo, vou acabar com esse ciclo de destruição que vocês causaram"),
        ("corpo seco", "Então me derrote garoto!! \n Não pense que vou deixar facíl, se você não conseguir me derrotar, não é o escolhido para derrotar Zanzara!"),
        ("Jaum Manel", "Mãe terra, me empreste um pouco de sua força!!")
        ),
    "carrasco da vigília": (
        ("carrasco da vigília", "Íncrivel, eu não esperava que tinha alguém capaz de chegar até mim! \n Mas não importa quantos de nós você derrote, enquanto Zanzara estiver livre, nós retornaremos!"),
        ("Jaum Manel", "Eu vou acabar com a sua maldição! \n Vou por um fim nessa guerra de uma vez por todas!"),
        ("carrasco da vigília", "Maldição? Então aquele fracote ainda busca um escolhido para conseguir fugir de seu destino? \n O que ele enxerga como 'Maldição' eu vejo como poder e com esse poder, me tornarei o guerreiro mais forte!!"),
        ("carrasco da vigília", "Não importa se você sabe da verdade, daqui você NÂO vai passar!! \n Não se ache especial, você não foi o primeiro e está longe de ser o último!"),
        ),
    "zanzara": (
        ("Jaum Manel", "Como você pode devastar tantos povos para continuar seu ciclo de ganância? \n Vocês nâo passam de MONSTROS!"),
        ("zanzara", "Monstros? me chama de monstro por salvar meu povo à beira da morte e lhes dar um propósito? \n Como uma recompensa por ter chegado tão longe, vou lhe contar um pouco de nossa história..."),
        ("zanzara", "Octav, abandonado para morrer por ser o sétimo filho de uma fámilia que tinha 6 mulheres. \n Pobrezinho, considerado um lobisomem, simplesmente por existir, teria um trágico fim se não fosse por MIM..."),
        ("zanzara", "A inseparável dupla Alvar e Tekks, quando os resgatei de uma terra já fadada a destruição, se tornaram amigos mesmo sendo de tribos rivais, fizeram de tudo para conseguir salvar suas terras do próprio povo..."),
        ("zanzara", "O nobre conde Tom, foi envenenado dentro do próprio castelo, não merecia esse terrível destino..."),
        ("zanzara", "Jozephino, o criativo goblinzinho, foi exilado por seu povo, apenas por pensar de maneira diferente..."),
        ("zanzara", "Jan-Pietro, você até me lembra um pouco dele... \n Ambos tem um coração puro, mas em tempos de guerra, de nada vale um coração inocente, ele foi traído e largado para trás pelo próprio povo..."),
        ("zanzara", "Labrro um poderoso soldado desde o berço, pobre homem, sempre sonhou em ser o mais forte, mas nunca conheceu nada além da guerra..."),
        ("zanzara", "Fadados à destruição tudo graças à ganancia e ao medo sem sentido de diversos povos.\n Se não fosse por MIM, nenhum deles estaria mais aqui."),
        ("zanzara", "E junto ao meu clã..\n Não, junto à minha família, vamos recriar tudo, poderemos ser aceitos em um mundo onde nunca tivemos espaço!!"), 
        ("Jaum Manel", "Sinto Muito, mas meu povo não vai ser um combustível para você continuar com suas batalhas sem sentido!!"),
        ("zanzara", "Seu povo não passa de um meio para um Fim. \n Meu clã já deve estar se reerguendo, vou te mostrar que sua coragem não passa de uma ilusão."),
        ),
    # Minibosses genéricos (caso apareçam no modo de jogo usado):
    "ogro ancestral": (),
    "cavaleiro caído": (),
    "behemoth de pedra": (),
}


def dialogue_for(enemy):
    """Obtém falas somente para confrontos contra chefes/minibosses."""
    if not (
        getattr(enemy, "is_miniboss", False)
        or getattr(enemy, "is_final_boss", False)
        or getattr(enemy, "boss_id", None)
    ):
        return ()
    name = getattr(enemy, "name", "").strip().lower()
    return tuple(BOSS_DIALOGUES.get(name, ()))
