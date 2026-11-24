"""Flags permanentes dos guias de gerenciamento, independentes da run."""
from src.systems.roguelite import transact

GUIDE_IDS = ('shop', 'backpack', 'workshop')


def normalize_guides(progress):
    flags = progress.setdefault('tutoriais_gerenciamento', {})
    if not isinstance(flags, dict) or any(type(value) is not bool for value in flags.values()):
        raise ValueError('Indicadores dos guias de gerenciamento inválidos.')
    for key in GUIDE_IDS:
        flags.setdefault(key, False)
    return flags


def complete_guide(manager, data, key):
    if key not in GUIDE_IDS:
        return False, 'Guia desconhecido.'
    def mutate():
        normalize_guides(data['progresso'])[key] = True
        return 'Guia registrado neste slot.'
    return transact(manager, data, mutate)
