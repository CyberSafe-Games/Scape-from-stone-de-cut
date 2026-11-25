"""Perfil visual transitório; o padrão nativo não muda."""
_compact=False
_remaining=24

def set_compact_effects(active):
    global _compact
    _compact=bool(active)

def begin_frame():
    global _remaining
    _remaining=24

def particle_amount(amount):
    global _remaining
    if not _compact:return amount
    count=min(6,max(0,amount),_remaining)
    _remaining-=count
    return count
