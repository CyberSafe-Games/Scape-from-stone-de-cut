"""Dados de um usuário que já dispensou os guias, para testes de outros fluxos."""
def guides_seen(data):
    flags = dict(shop=True, backpack=True, workshop=True)
    data['progresso']['tutoriais_gerenciamento'] = flags
    if 'perfil' in data:
        data['perfil']['tutoriais_gerenciamento'] = dict(flags)
    return data
