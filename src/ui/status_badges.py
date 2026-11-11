import pygame
from src.ui.helpers import draw_text, draw_panel, wrap_text

INFO = {
 'fire': ('Fogo', '3 de dano por intensidade ao fim do turno; atinge Escudo. Máximo: 3 intensidades.'),
 'poison': ('Veneno', 'Dano direto à vida no fim do turno; ignora Escudo. As aplicações das novas cartas acumulam acúmulos.'),
 'bleed': ('Sangramento', 'Dano direto igual aos acúmulos no primeiro ataque de cada turno. Não repete em ações adicionais do chefe.'),
 'burn': ('Queimadura', 'Cada acúmulo causa 1 de dano direto à vida ao fim do turno; dura 3 turnos por aplicação.'),
 'vulnerable': ('Fragilidade', 'Recebe 25% a mais de dano de ataques; não amplifica efeitos de dano contínuo.'),
 'weak': ('Fraqueza', 'Causa 25% a menos de dano; a duração é contada em turnos do afetado.'),
 'aura': ('Aura Rubra', 'Dano adicional por ataque. Reaplicar renova a duração, sem acumular bônus.'),
 'totem': ('Totem Protetor', 'Anula o próximo ataque completo. Dano de efeitos não consome o Totem.'),
 'shield': ('Escudo', 'Absorve dano. Cada aplicação dura 2 turnos do dono; receber mais não renova o Escudo antigo.'),
 'weakness': ('Fraqueza', 'Causa 25% a menos de dano. Mantém a duração original da ultimate.'),
 'strength': ('Força', 'Bônus de dano durante o combate.'),
 'energy': ('Energia futura', 'Energia extra no próximo turno. O total de energia disponível não ultrapassa 8.'),
 'stun': ('Atordoamento', 'Pula o próximo turno inteiro do afetado.'),
 'debuff_immunity': ('Imunidade', 'Impede a aplicação de novos efeitos negativos enquanto durar.'),
 'no_heal': ('Sem cura', 'Impede o afetado de recuperar vida durante o próximo turno.'),
 'no_block': ('Sem escudo', 'Impede o afetado de receber Escudo enquanto durar.'),
 'attack_burn': ('Chuva de Faíscas', 'Cada ataque do usuário aplica Queimadura ao alvo neste turno.'),
 'burn_on_action': ('Armadilha de Brasa', 'Cada ação do afetado aplica Queimadura nele mesmo.'),
 'poison_on_damage': ('Sangue Tóxico', 'Cada dano à vida sofrido aplica Veneno ao afetado neste turno.'),
 'poison_multiplier': ('Veneno dobrado', 'O dano de Veneno do próximo turno é duplicado.'),
 'double_bleed': ('Dança da Lâmina Rubra', 'As cartas do usuário aplicam o dobro de Sangramento neste turno.'),
 'attack_lock': ('Ataques bloqueados', 'Você não pode jogar cartas de ataque durante o turno indicado.'),
}


def draw_status_badges(surface, combatant, x, y, width, assets, mouse):
    states = [(name, state['turns'] or '1', state['potency']) for name, state in combatant.statuses.items()]
    if combatant.block:
        states.insert(0, ('shield', combatant.block, combatant.block_turns))
    if combatant.strength: states.append(('strength', combatant.strength, 0))
    if combatant.weak_turns and 'weak' not in combatant.statuses:
        states.append(('weakness', combatant.weak_turns, 0))
    if combatant.attack_lock_turns or combatant.attack_lock_pending:
        states.append(('attack_lock', combatant.attack_lock_turns or combatant.attack_lock_pending, 0))
    if combatant.next_turn_energy: states.append(('energy', combatant.next_turn_energy, 0))
    per_row = max(1, width // 66)
    for i, (name, count, potency) in enumerate(states):
        rect = pygame.Rect(x + (i % per_row) * 66, y + (i // per_row) * 38, 63, 35)
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(surface, (12, 20, 20), rect, border_radius=6)
        pygame.draw.rect(surface, (179, 135, 72) if hovered else (73, 72, 52), rect, 2, border_radius=6)
        icon = assets.get_status_icon(name)
        if icon is not None:
            surface.blit(pygame.transform.smoothscale(icon, (32, 32)), rect.move(2, 2))
        draw_text(surface, str(count), assets.small_font, (234, 220, 184), rect.right - 17, rect.centery, center=True)
        if hovered:
            title, text = INFO[name]
            if name in combatant.statuses:
                text += f" Restam {combatant.statuses[name]['turns']} turnos." if name != 'totem' else ''
                if name == 'fire': text += f' Intensidade: {potency}.'
                if name == 'poison': text += f' Dano por turno: {potency}.'
                if name == 'aura': text += f' Bônus de dano: +{potency}.'
            elif name == 'shield': text += f' Duração máxima restante: {potency} turnos.'
            lines = wrap_text(text, assets.small_font, 465)
            box = pygame.Rect(min(1395, max(18, x)), 320, 507, 72 + len(lines) * 29)
            draw_panel(surface, box, fill=(9, 16, 17, 248), border=(171, 125, 66), radius=11)
            draw_text(surface, title, assets.font, (240, 213, 151), box.x + 20, box.y + 15)
            for j, line in enumerate(lines):
                draw_text(surface, line, assets.small_font, (214, 218, 202), box.x + 20, box.y + 59 + j * 29)
