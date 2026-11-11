"""Prévia do kit completo no combate, sem acessar saves."""
import os
import sys
import math
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_zanzara, choose_next_action


def main():
    from PIL import Image, ImageDraw
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1), draw_fullscreen_button=lambda *_: None)
    scene = BattleScene(None, window, assets, selected_level=7)
    scene.engine.level = 7
    scene.engine.enemy = boss = create_zanzara()
    scene.engine.player.hp = scene.engine.player.max_hp = 999
    choose_next_action(boss)
    sequence, posters = [], []
    canvas = pygame.Surface((1920, 1080))

    def capture(duration, label, poster=False):
        for i in range(math.ceil(duration/70)+1):
            if i:
                scene.update(70)
            scene.draw(canvas)
            im = Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB'))
            small = im.resize((896, 504), Image.Resampling.LANCZOS)
            ImageDraw.Draw(small).text((15, 115), label, fill='#ffe29c', stroke_width=1, stroke_fill='#101010')
            sequence.append(small)
            if poster and i == round(duration*.80/70):
                posters.append(im.resize((768, 432), Image.Resampling.LANCZOS))

    capture(1400, 'Zanzara · repouso')
    scene.entity_view.trigger_flash('enemy')
    capture(400, 'Reação de dano')
    for action in boss.actions+[boss.special_action]:
        scene.engine.state = 'player_turn'
        boss.hp = min(boss.max_hp, 160) if action.action_type == 'buff' else boss.hp
        scene.engine.end_turn()
        boss.set_intent(action.action_type, action.value, action)
        scene.engine.enemy_actions_remaining = 1
        scene.engine.enemy_turn()
        view = scene.entity_view
        duration = view.enemy_attack_duration if action.action_type == 'attack' else view.enemy_action_duration
        capture(duration, {'atk1': 'Foice Sombria', 'atk2': 'Passo do Barqueiro', 'atk3': 'Travessia Final' if action is boss.special_action else 'Grilhoes das Almas'}.get(action.visual_effect, 'Buff legado: regras preservadas'), poster=True)
    atlas = Image.new('RGB', (768*2, 432*3), '#13241d')
    for i, im in enumerate(posters):
        atlas.paste(im, ((i % 2)*768, (i//2)*432))
    atlas.save(ROOT/'docs/zanzara_necromante_combate.png')
    palette = atlas.quantize(colors=224)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in sequence]
    frames[0].save(ROOT/'docs/zanzara_necromante_acao.gif', save_all=True, append_images=frames[1:], duration=70, loop=0, optimize=True)
    pygame.image.save(canvas, str(ROOT/'docs/zanzara_necromante_batalha.png'))
    print('Prévia de Zanzara exportada.')
    pygame.quit()


def interactive():
    """Teste visual isolado: não lê nem grava progresso da campanha."""
    os.environ.pop('SDL_VIDEODRIVER', None)
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('Zanzara - Revisao 13 - dificuldade')
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1), draw_fullscreen_button=lambda *_: None)
    scene = BattleScene(None, window, assets, selected_level=7)
    scene.engine.enemy = create_zanzara()
    scene.engine.level = 7
    choose_next_action(scene.engine.enemy)
    scene.engine.player.hp = scene.engine.player.max_hp = 999
    scene.engine.state = 'player_turn'
    canvas = pygame.Surface((1920, 1080))
    clock = pygame.time.Clock()
    actions = {pygame.K_1: ('atk1', False, 'Foice Sombria'),
               pygame.K_2: ('atk2', False, 'Passo do Barqueiro'),
               pygame.K_3: ('atk3', False, 'Grilhoes das Almas'),
               pygame.K_4: ('atk3', True, 'Travessia Final')}
    label = 'Repouso'
    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in actions:
                action, ultimate, label = actions[event.key]
                if scene.engine.enemy.hp <= 0:
                    continue
                boss = scene.engine.enemy
                move = boss.special_action if ultimate else boss.actions[{'atk1':0,'atk2':1,'atk3':2}[action]]
                scene.entity_view.enemy_flash = 0
                boss.energy = boss.max_energy
                boss.set_intent(move.action_type,move.value,move)
                scene.engine.enemy_actions_remaining = 1
                scene.engine.state = 'enemy_turn'
                scene.engine.enemy_turn()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                if scene.engine.enemy.hp > 0:
                    scene.engine.enemy.take_damage(1)
                    scene.entity_view.trigger_flash('enemy')
                    label = 'Reacao ao dano'
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                scene.engine.enemy.hp = 0
                scene.entity_view.attacker = None
                scene.entity_view.player_action = None
                scene.entity_view.pending_enemy_hit_at = None
                scene.entity_view.enemy_flash = 0
                label = 'Derrota - R restaura'
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                from src.ui.entity_view import EntityView
                scene.entity_view = EntityView(assets)
                scene.engine.enemy = create_zanzara()
                scene.engine.player.hp = 999
                scene.engine.player.reset_combat_effects()
                scene.engine.state = 'player_turn'
                choose_next_action(scene.engine.enemy)
                label = 'Repouso'
        scene.entity_view.update(dt)
        scene.draw(canvas)
        font = assets.get_font('small')
        text = font.render('REVISAO 13 | 1 Foice | 2 Passo | 3 Grilhoes | 4 Travessia | Esc sair - ' + label, True, (210, 255, 215))
        canvas.blit(text, (30, 175))
        extra = font.render('H: receber golpe | D: derrota | R: restaurar | 1-4: executar habilidades (sem salvar)',True,(185,220,194))
        canvas.blit(extra,(30,205))
        screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    interactive() if '--interactive' in sys.argv else main()
