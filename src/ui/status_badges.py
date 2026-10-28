import pygame
from src.ui.helpers import draw_text, draw_panel, wrap_text

INFO = {
 'fire': ('Fogo', '3 de dano por intensidade ao fim do turno; atinge Escudo. Máximo: 3 intensidades.'),
 'poison': ('Veneno', 'Dano direto à vida no fim do turno; ignora Escudo e Totem. Reaplicar renova a duração.'),
 'bleed': ('Sangramento', '4 de dano direto à vida no primeiro ataque de cada turno. Não repete em ações adicionais do chefe.'),
 'vulnerable': ('Fragilidade', 'Recebe 25% a mais de dano de ataques; não amplifica efeitos de dano contínuo.'),
 'aura': ('Aura Rubra', '+8 de dano por ataque. Reaplicar renova a duração, sem acumular bônus.'),
 'totem': ('Totem Protetor', 'Anula o próximo ataque completo. Dano de efeitos não consome o Totem.'),
 'shield': ('Escudo', 'Absorve dano. Cada aplicação dura 2 turnos do dono; receber mais não renova o Escudo antigo.'),
 'weakness': ('Fraqueza', 'Causa 25% a menos de dano. Mantém a duração original da ultimate.'),
 'strength': ('Força', 'Bônus de dano durante o combate.'),
 'energy': ('Energia futura', 'Energia extra no próximo turno. O total de energia disponível não ultrapassa 8.'),
}


def draw_status_badges(surface, combatant, x, y, width, assets, mouse):
    states = [(name, state['turns'] or '1', state['potency']) for name, state in combatant.statuses.items()]
    if combatant.block:
        states.insert(0, ('shield', combatant.block, combatant.block_turns))
    if combatant.strength: states.append(('strength', combatant.strength, 0))
    if combatant.weak_turns: states.append(('weakness', combatant.weak_turns, 0))
    if combatant.next_turn_energy: states.append(('energy', combatant.next_turn_energy, 0))
    per_row = max(1, width // 44)
    for i, (name, count, potency) in enumerate(states):
        rect = pygame.Rect(x + (i % per_row) * 44, y + (i // per_row) * 25, 42, 23)
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(surface, (12, 20, 20), rect, border_radius=4)
        pygame.draw.rect(surface, (179, 135, 72) if hovered else (73, 72, 52), rect, 1, border_radius=4)
        icon = assets.get_status_icon(name)
        if icon is not None:
            surface.blit(pygame.transform.smoothscale(icon, (21, 21)), rect.move(1, 1))
        draw_text(surface, str(count), assets.small_font, (234, 220, 184), rect.right - 11, rect.centery, center=True)
        if hovered:
            title, text = INFO[name]
            if name in combatant.statuses:
                text += f" Restam {combatant.statuses[name]['turns']} turnos." if name != 'totem' else ''
                if name == 'fire': text += f' Intensidade: {potency}.'
                if name == 'poison': text += f' Dano por turno: {potency}.'
            elif name == 'shield': text += f' Duração máxima restante: {potency} turnos.'
            lines = wrap_text(text, assets.small_font, 310)
            box = pygame.Rect(min(930, max(12, x)), 213, 338, 48 + len(lines) * 19)
            draw_panel(surface, box, fill=(9, 16, 17, 248), border=(171, 125, 66), radius=7)
            draw_text(surface, title, assets.font, (240, 213, 151), box.x + 13, box.y + 10)
            for j, line in enumerate(lines):
                draw_text(surface, line, assets.small_font, (214, 218, 202), box.x + 13, box.y + 39 + j * 19)
