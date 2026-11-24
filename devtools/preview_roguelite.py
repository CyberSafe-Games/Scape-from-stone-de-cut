"""Prévia da interface roguelite com saves temporários, sem tocar slots reais."""
import argparse
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--output', default='tools/roguelite-qa')
    args = parser.parse_args()
    if args.smoke:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    import pygame
    from src.core.asset_manager import AssetManager
    from src.core.window import WindowManager
    from src.core.scene_manager import SceneManager
    from src.scenes.roguelite_scene import RogueliteScene
    from src.scenes.shop_scene import ShopScene
    from src.scenes.backpack_scene import BackpackScene
    from src.scenes.battle_scene import BattleScene
    from src.systems.save_manager import SaveManager
    from src.systems.card_catalog import AVAILABLE_CARD_POOL
    from src.systems.roguelite import upgrade_copy
    pygame.init()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    window, scenes, assets = WindowManager(), SceneManager(), AssetManager()
    with tempfile.TemporaryDirectory() as folder:
        manager = SaveManager(folder)
        data = manager.create_save('preview')
        p = data['progresso']
        p['tutorial_concluido'] = True
        # Este piloto inspeciona os layouts; os guias têm preview próprio.
        p['tutoriais_gerenciamento'] = dict.fromkeys(('shop', 'backpack', 'workshop'), True)
        p['moedas'] = 1000
        p['vida'] = 25
        p['cartas_colecao'] = [c.name for c in AVAILABLE_CARD_POOL]
        p['materials'] = {c.name: 6 for c in AVAILABLE_CARD_POOL}
        manager.save(data)
        upgrade_copy(manager, data, p['copies'][0]['id'])
        factory_args = (scenes, window, assets, manager, data)
        gallery = [ShopScene(*factory_args), RogueliteScene(*factory_args), BackpackScene(*factory_args)]
        for name, scene in zip(('loja', 'oficina', 'mochila'), gallery):
            scene.draw(window.screen)
            pygame.image.save(window.screen, output / f'{name}.png')
            if name == 'mochila':
                scene.window_manager.get_virtual_mouse_pos = lambda: scene.slots[0].center
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'mochila_hover_lv2.png')
                scene.window_manager.get_virtual_mouse_pos = lambda: (-1, -1)
                scene.tab = 'ultimates'
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'mochila_ultimates.png')
                scene.tab = 'deck'
                original = list(scene.draft_slots)
                scene.draft_slots = [None] * len(original)
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'mochila_vazia.png')
                from src.systems.deck_loadout import build_random_deck
                scene.draft_slots = build_random_deck(p['cartas_colecao'])
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'mochila_completa.png')
                scene.draft_slots = original
                scene.level_filter = 2
                scene._set_page(0)
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'mochila_filtro_lv2.png')
                scene.level_filter = None
                scene._set_page(0)
                # Restaura o método real; o piloto continua clicável.
                del scene.window_manager.get_virtual_mouse_pos
            if name == 'loja':
                rect = scene.heal_button
                before = data['progresso']['moedas']
                scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                    button=1, pos=(round(rect.centerx * 2 / 3), round(rect.centery * 2 / 3))))
                assert data['progresso']['moedas'] == before - 30
                assert data['progresso']['vida'] == 45
                assert data['progresso']['melhorias_vida_run'] == 0
                assert data['progresso']['curas_loja_run'] == 1
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'loja_segunda_cura.png')
                before = data['progresso']['moedas']
                scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                    button=1, pos=(round(rect.centerx * 2 / 3), round(rect.centery * 2 / 3))))
                assert data['progresso']['moedas'] == before - 45
                assert data['progresso']['vida'] == 60
                data['progresso']['vida'] = 10  # representa dano em outro encontro
                manager.save(data)
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'loja_terceira_cura.png')
                before = data['progresso']['moedas']
                scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                    button=1, pos=(round(rect.centerx * 2 / 3), round(rect.centery * 2 / 3))))
                assert data['progresso']['moedas'] == before - 60
                assert data['progresso']['vida'] == 30
                assert data['progresso']['curas_loja_run'] == 3
                scene.draw(window.screen)
                pygame.image.save(window.screen, output / 'loja_curas_esgotadas.png')
                before = data['progresso']['moedas']
                scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                    button=1, pos=(round(rect.centerx * 2 / 3), round(rect.centery * 2 / 3))))
                assert data['progresso']['moedas'] == before
                assert data['progresso']['curas_loja_run'] == 3
            if name == 'oficina':
                rect = scene.material_button
                before = data['progresso']['moedas']
                scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                    button=1, pos=(round(rect.centerx * 2 / 3), round(rect.centery * 2 / 3))))
                assert data['progresso']['moedas'] == before - 15
        battle = BattleScene(*factory_args, map_mode=True, selected_level=1,
                             encounter_kind='road', encounter_index=0)
        battle.boss_dialogue = None
        battle.draw(window.screen)
        pygame.image.save(window.screen, output / 'batalha.png')
        original_energy = battle.engine.energy
        battle.engine.equip_ultimate('rugido_da_floresta')
        battle.engine.player.ultimate_charge = 20
        battle.engine.player.energy = 1
        battle.draw(window.screen)
        pygame.image.save(window.screen, output / 'especial_sem_energia.png')
        rect = battle.ultimate_hand_rect
        battle.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
            button=1, pos=(round(rect.centerx * 2 / 3), round(rect.centery * 2 / 3))))
        assert battle.engine.player.ultimate_charge == 20
        assert battle.engine.energy == 1
        battle.engine.player.energy = 2
        battle.draw(window.screen)
        pygame.image.save(window.screen, output / 'especial_custo2.png')
        battle.engine.equip_ultimate('mana_ancestral')
        from src.systems.roguelite import instance_card
        battle.engine.deck_manager.hand = [instance_card({
            'id': f'preview-axes-{level}', 'name': 'Machados Gêmeos', 'level': level})
            for level in (1, 2)]
        battle.draw(window.screen)
        pygame.image.save(window.screen, output / 'mana_custo2_machados_custo5.png')
        battle.engine.player.ultimate_charge = 0
        battle.engine.player.energy = original_energy
        revised_names = ('Investida', 'Máscara Ancestral', 'Amuleto Dissipador', 'Surto de Energia')
        battle.engine.deck_manager.hand = [instance_card({
            'id': f'preview-revised-{i}', 'name': name, 'level': 2})
            for i, name in enumerate(revised_names)]
        battle.engine.player.energy_max = battle.engine.player.energy = 8
        battle.draw(window.screen)
        pygame.image.save(window.screen, output / 'cartas_revisadas_surto_sem_ganho.png')
        battle.engine.player.energy_max = battle.engine.player.energy = 5
        battle.draw(window.screen)
        pygame.image.save(window.screen, output / 'cartas_revisadas_surto_ganho.png')
        battle.engine.enemy.hp = 0
        battle.engine._on_enemy_defeated()
        assert battle._persist_logical_state()
        battle._outcome_elapsed = battle.VICTORY_POSE_MS
        battle._draw_victory(window.screen)
        pygame.image.save(window.screen, output / 'recompensa.png')
        battle.reward_view.show_materials = True
        battle._draw_victory(window.screen)
        pygame.image.save(window.screen, output / 'materiais.png')
        (_, name), rect = next(battle.reward_view.offers(battle.engine, data['progresso']))
        before = data['progresso']['materials'][name]
        for target in (rect, battle.reward_view.CONFIRM):
            battle.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                button=1, pos=(round(target.centerx * 2 / 3), round(target.centery * 2 / 3))))
        battle.update(battle.reward_view.CONFIRM_MS)
        assert data['progresso']['materials'][name] == before + 1
        assert data['progresso']['combat_snapshot'] is None
        manager.end_run(data, 7)
        data['perfil']['fragmentos'] = 20
        manager.save(data)
        preparation = RogueliteScene(*factory_args, preparation=True)
        preparation.draw(window.screen)
        pygame.image.save(window.screen, output / 'preparacao.png')
        print('SMOKE OK: loja, oficina, mochila, batalha, recompensa, materiais e preparação.')
        if not args.smoke:
            scenes.change_scene(preparation)
            clock = pygame.time.Clock()
            running = True
            while running:
                dt = clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    else:
                        scenes.current_scene.handle_event(event)
                scenes.current_scene.update(dt)
                scenes.current_scene.draw(window.screen)
                window.present()
    pygame.quit()


if __name__ == '__main__':
    main()
