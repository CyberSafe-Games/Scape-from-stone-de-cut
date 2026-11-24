"""Pilotos independentes de áudio e vitória, com saves temporários."""

import argparse
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROAD_PREVIEWS = {
    "vinimuth": ("Vinimuth", 7),
    "guerreiro": ("Guerreiro da Mata", 2),
    "morcego": ("Morcego Sombrio", 5),
    "crocodilo": ("Crocodilo Abissal", 4),
    "viniurgo": ("Viniurgo", 1),
    "macaco": ("Macaco Selvagem", 2),
    "golem": ("Golem das Ruínas", 3),
    "lagarto": ("Lagarto Couraçado", 3),
    "putrefato": ("Putrefato do Pântano", 4),
    "esqueleto": ("Esqueleto Saqueador", 5),
    "centauro": ("Centauro Vigia", 6),
    "lutador": ("Lutador Mascarado", 6),
    "mago": ("Mago do Santuário", 7),
}
BOSS_PREVIEWS = {"octav": 1, "jozephino": 3, "sir-thomas": 4, "jan-pietro": 5, "labrro": 6}
LETHAL_ARROW_CASES = ("vitoria", "zanzara", "tekks", "tekks-final", "recompensa", "final-musical",
                     *ROAD_PREVIEWS, *BOSS_PREVIEWS)
DEBUFF_SOUNDS = {
    "veneno": "gameplay.status.poison_tick",
    "sangramento": "gameplay.status.bleed_tick",
    "choque": "gameplay.status.shock_tick",
    "queimadura": "gameplay.status.burn_tick",
}
CUTSCENE_CASES = ("texto", "intro", "epilogo")
REVIEW_CASES = {
    "rugido": "Rugido",
    "mangual": "Mangual",
    "texto": "Diálogos",
    "intro": "Abertura",
    "final-musical": "Zanzara e epílogo",
    "derrota": "Game Over",
    "tutorial": "Tutorial",
    "recompensa": "Recompensa",
}
REVIEW_DESCRIPTIONS = (
    "Ativação e som de chama quando o avatar é lançado",
    "A: Varredura do Mangual   S: Abalo da Floresta",
    "Som de avanço das falas, com a música silenciada",
    "Trilha de batalha; troca quando Zanzara aparece",
    "Faixa de Zanzara, silêncio e trilha de despedida",
    "Golpe fatal do inimigo e som de Game Over",
    "Espaço: ataque do Slime   V: vitória do tutorial",
    "Vitória, bolsa de ouro e seleção no altar",
)
REVIEW_SOUNDS = {
    **DEBUFF_SOUNDS,
    "rugido": "gameplay.attack.fireball",
    "mangual": "gameplay.attack.shield_break",
    "mangual-abalo": "gameplay.attack.shield_break",
    "golem-plasma": "gameplay.boss.goblin.beam",
    "golem-escudo": "gameplay.boss.guardian.stone",
    "texto": "ui.navigate",
    "derrota": "gameplay.game_over",
    "tutorial": "gameplay.enemy.slime",
    "tutorial-vitoria": "gameplay.victory",
}

PILOTS = {
    "vitoria": ("Vitória e bolsa de ouro",
                ("vitoria", "zanzara", "tekks", "vinimuth", "guerreiro", "morcego", "crocodilo")),
    "derrotas-comuns": ("Derrotas dos inimigos comuns", ("morcego", "vitoria",
                         *(name for name in ROAD_PREVIEWS if name != "morcego"))),
    "derrotas-chefes": ("Derrotas dos chefes", (*BOSS_PREVIEWS, "tekks", "tekks-final", "zanzara")),
    "recompensa": ("Escolha, materiais e pulo", ("recompensa",)),
    "rugido": ("Impacto do Rugido da Floresta", ("rugido",)),
    "debuffs": ("Áudio dos debuffs", tuple(DEBUFF_SOUNDS)),
    "queimadura": ("Cauda de chama da Queimadura", ("queimadura",)),
    "dialogos": ("Transição de texto", ("texto",)),
    "abertura": ("Trilha da abertura", ("intro",)),
    "trilha": ("Da floresta à invasão e ao epílogo", ("intro", "epilogo")),
    "mangual": ("Golpes do Guerreiro da Mata", ("mangual", "mangual-abalo")),
    "golem-audio": ("Escudo e plasma do Golem das Ruínas", ("golem-plasma", "golem-escudo")),
    "derrota": ("Impacto e Game Over", ("derrota",)),
    "tutorial": ("Áudio no tutorial", ("tutorial", "tutorial-vitoria")),
    "polimento-final": ("Revisão de áudio", tuple(REVIEW_CASES)),
    "loja-epilogo": ("Loja e epílogo", ("loja", "final-musical")),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", choices=PILOTS)
    parser.add_argument("--case", help="Abre diretamente um dos testes do piloto.")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    import pygame
    from main import configure_audio
    from src.config.cutscenes import FINAL_CUTSCENE, INTRO_CUTSCENE
    from src.config.music import MUSIC_VOLUME
    from src.config.settings import FPS, HEIGHT, WIDTH
    from src.core.asset_manager import AssetManager
    from src.core.audio_manager import AudioManager
    from src.core.scene_manager import SceneManager
    from src.core.window import WindowManager
    from src.scenes.battle_scene import BattleScene
    from src.scenes.cutscene_scene import CutsceneScene
    from src.scenes.shop_scene import ShopScene
    from src.scenes.tutorial_scene import TutorialScene
    from src.systems.card_catalog import CARD_BY_NAME
    from src.systems.enemy_factory import create_alvaro_tex, create_point_enemy, create_road_enemy, create_zanzara
    from src.systems.roguelite import UPGRADE_PRICES, upgrade_copy
    from src.systems.save_manager import SaveManager
    from src.systems.territory_map import ROAD_FIGHTS, TERRITORY_IDS
    from src.ui.dark_fantasy_theme import divider, panel
    from src.ui.helpers import draw_text
    from unittest.mock import patch

    pygame.init()
    title, cases = PILOTS[args.pilot]
    if args.case is not None and args.case not in cases:
        parser.error(f"Teste indisponível nesse piloto: {args.case}")
    window = WindowManager(title=f"Piloto  |  {title}")
    assets = AssetManager()
    audio = AudioManager(music_volume=MUSIC_VOLUME)
    configure_audio(audio)
    scenes = SceneManager(audio)

    def draw_shortcuts(surface):
        rect = pygame.Rect(420, 180, 1080, 720)
        panel(surface, rect, highlighted=True, fill=(8, 15, 12, 248))
        title_color = (233, 192, 106)
        body_color = (230, 222, 197)
        draw_text(surface, "Atalhos do piloto", assets.title_font, title_color,
                  rect.centerx, rect.y + 58, center=True)
        divider(surface, rect.x + 56, rect.right - 56, rect.y + 114)
        for number, (name, description) in enumerate(
            zip(REVIEW_CASES.values(), REVIEW_DESCRIPTIONS), 1
        ):
            y = rect.y + 139 + (number - 1) * 55
            draw_text(surface, f"{number}  {name}", assets.font, title_color, rect.x + 68, y)
            draw_text(surface, description, assets.small_font, body_color, rect.x + 345, y + 4)
        divider(surface, rect.x + 56, rect.right - 56, rect.bottom - 129)
        draw_text(surface, "Espaço executa ou avança  ·  R reinicia  ·  ←/→ troca o teste",
                  assets.small_font, body_color, rect.centerx, rect.bottom - 92, center=True)
        draw_text(surface, "F1 abre ou fecha esta legenda  ·  Esc sai do piloto",
                  assets.small_font, title_color, rect.centerx, rect.bottom - 52, center=True)

    def setup(case, folder):
        audio.set_music_volume(0 if case in DEBUFF_SOUNDS or case == "texto" else MUSIC_VOLUME)
        if case == "loja":
            manager = SaveManager(tempfile.mkdtemp(dir=folder))
            data = manager.create_save("preview")
            data["progresso"]["moedas"] = 1000
            manager.save(data)
            scene = ShopScene(scenes, window, assets, manager, data)
            scenes.change_scene(scene)
            return scene
        if case in CUTSCENE_CASES:
            frames = FINAL_CUTSCENE if case == "epilogo" else INTRO_CUTSCENE
            scene = CutsceneScene(scenes, window, assets, frames, lambda: None)
            scenes.change_scene(scene)
            return scene
        if case in ("tutorial", "tutorial-vitoria"):
            scene = TutorialScene(scenes, window, assets)
            scenes.change_scene(scene)
            return scene
        if case in ("recompensa", "final-musical"):
            manager = SaveManager(tempfile.mkdtemp(dir=folder))
            data = manager.create_save("preview")
            progress = data["progresso"]
            if case == "recompensa":
                copy = progress["copies"][0]
                progress["materials"][copy["name"]] = 4
                progress["moedas"] += UPGRADE_PRICES[copy["name"]]
                manager.save(data)
                upgraded, message = upgrade_copy(manager, data, copy["id"])
                assert upgraded, message
                battle = BattleScene(scenes, window, assets, manager, data, map_mode=True,
                                     selected_level=1, encounter_kind="road", encounter_index=0)
            else:
                progress["andar"] = len(TERRITORY_IDS)
                progress["territorios_concluidos"] = list(TERRITORY_IDS[:-1])
                progress["territorios_desbloqueados"] = list(TERRITORY_IDS)
                progress["encontros_por_territorio"] = dict.fromkeys(TERRITORY_IDS, ROAD_FIGHTS)
                manager.save(data)
                battle = BattleScene(scenes, window, assets, manager, data, map_mode=True,
                                     selected_level=len(TERRITORY_IDS))
        else:
            battle = BattleScene(scenes, window, assets)
        battle.boss_dialogue = None
        engine = battle.engine
        if case == "zanzara":
            engine.enemy = create_zanzara()
        elif case in ("tekks", "tekks-final"):
            engine.enemy = create_alvaro_tex(phase=2 if case == "tekks-final" else 1)
        elif case in BOSS_PREVIEWS:
            engine.enemy = create_point_enemy(BOSS_PREVIEWS[case])
        elif case != "final-musical":
            road_case = {"mangual": "guerreiro", "mangual-abalo": "guerreiro",
                         "golem-plasma": "golem", "golem-escudo": "golem"}.get(case, case)
            name, level = ROAD_PREVIEWS.get(road_case, ("Slime", 1))
            with patch("src.systems.enemy_factory.random.choice", return_value=name):
                engine.enemy = create_road_enemy(level)
        engine.player.energy = 8
        engine.deck_manager.hand = [CARD_BY_NAME["Disparo de Arco"].copy()]
        if case in LETHAL_ARROW_CASES:
            engine.enemy.hp = 1
        elif case == "rugido":
            engine.player.unlock_ultimate("rugido_da_floresta")
            assert engine.equip_ultimate("rugido_da_floresta")
            engine.player.ultimate_charge = engine.ultimate_threshold
            engine.enemy.hp = 100
        elif case == "veneno":
            engine.player.add_stacks("poison", 2)
            engine.enemy.apply_status("stun", 1, 1)
        elif case == "sangramento":
            engine.player.add_stacks("bleed", 2)
        elif case == "choque":
            engine.enemy.apply_status("stun", 1, 1)
        elif case == "queimadura":
            engine.player.apply_status("burn", 2, 3)
            engine.enemy.apply_status("stun", 1, 1)
        elif case == "derrota":
            engine.player.hp = 1
        scenes.change_scene(battle)
        return battle

    def trigger(case, scene, enemy_attack=0):
        engine = scene.engine
        if case == "rugido":
            assert engine.activate_ultimate()
            scene.play_ui_sound("gameplay.ultimate_activate")
        elif case == "sangramento":
            engine._bleed_on_attack(engine.player)
        elif case in ("tutorial", "tutorial-vitoria"):
            scene.overlay.finish()
            scene.overlay.update(1000)
            if case == "tutorial-vitoria":
                engine.enemy.hp = 1
                hand = engine.deck_manager.hand
                assert engine.play_card(next(index for index, card in enumerate(hand)
                                             if card.name == "Soco Simples"))
            else:
                engine.end_turn()
        elif case in ("veneno", "choque", "queimadura", "mangual", "mangual-abalo",
                      "golem-plasma", "golem-escudo", "derrota"):
            engine.end_turn()
            if case == "choque" and engine.state == "enemy_turn":
                engine.player.add_stacks("shock", 2, turns=1)
            if engine.state == "enemy_turn":
                if case == "golem-escudo":
                    enemy_attack = 1
                action = engine.enemy.actions[enemy_attack]
                engine.enemy.set_intent(action.action_type, action.value, action)
        else:
            assert engine.play_card(0)

    try:
        with tempfile.TemporaryDirectory() as folder:
            if args.smoke:
                for case in cases:
                    scene = setup(case, folder)
                    if case == "loja":
                        name = next(iter(scene.card_rects))
                        for mouse in (scene.card_rects[name].center, scene.offer_rects[name].center):
                            with patch.object(window, "get_virtual_mouse_pos", return_value=mouse):
                                scenes.draw(window.screen)
                        continue
                    if case == "rugido":
                        assert scene.engine.active_ultimate_id == "rugido_da_floresta"
                        assert scene.engine.ultimate_ready
                        scenes.draw(window.screen)
                    channels = []
                    play_sfx = audio.play_sfx

                    def track_preview(sound_id, **kwargs):
                        channel = play_sfx(sound_id, **kwargs)
                        if sound_id == REVIEW_SOUNDS.get(case):
                            channels.append(channel)
                        return channel

                    if case in REVIEW_SOUNDS:
                        audio.stop_all_sfx()
                        audio.play_sfx = track_preview
                    if case not in CUTSCENE_CASES:
                        trigger(case, scene, enemy_attack=int(case == "mangual-abalo"))
                    checked_banner = False
                    contexts = set()
                    for frame in range(1600 if case in ("intro", "epilogo") else 380):
                        scenes.update(16)
                        if (case in ("vinimuth", "tutorial-vitoria") and not checked_banner
                                and scene._outcome_elapsed is not None
                                and scene._outcome_elapsed >= scene.VICTORY_BANNER_MS):
                            assert not scene._victory_ready
                            scenes.draw(window.screen)
                            checked_banner = True
                        if case in CUTSCENE_CASES and frame % 9 == 0 and scenes.current_scene is scene:
                            contexts.add(scene.music_context)
                            scenes.handle_event(pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_SPACE
                            ))
                    scenes.draw(window.screen)
                    if case in REVIEW_SOUNDS:
                        audio.play_sfx = play_sfx
                        assert channels and all(channel is not None for channel in channels), (case, channels)
                        if case in DEBUFF_SOUNDS:
                            assert len(channels) == 1, (case, channels)
                    if case in LETHAL_ARROW_CASES and case not in ("tekks", "final-musical"):
                        assert scene._victory_ready and scene._reward_gold > 0, case
                    if case in ("vinimuth", "tutorial-vitoria"):
                        assert checked_banner
                    if case == "recompensa":
                        view = scene.reward_view
                        progress = scene.save_data["progresso"]
                        view.click(view.MATERIALS.center, scene.engine, progress)
                        option, tile = next(view.offers(scene.engine, progress))
                        view.click(tile.center, scene.engine, progress)
                        assert view.click(view.CONFIRM.center, scene.engine, progress) == option
                        view.draw(window.screen, scene.engine, progress, scene._reward_gold, tile.center)
                    if case == "derrota":
                        assert scene._game_over_ready
                    if case == "tekks":
                        assert scene.engine.enemy.phase == 2 and not scene._reward_gold
                    if case == "intro":
                        assert contexts == {"battle", "boss"}, contexts
                    if case == "epilogo":
                        assert contexts == {"final_boss", None, "farewell"}, contexts
                    if case == "final-musical":
                        assert scene.music_context == "final_boss"
                        assert not scene._victory_ready
                        assert isinstance(scenes.current_scene, CutsceneScene)
                        assert scenes.current_scene.music_context == "final_boss"
                        assert scene.save_data["progresso"]["estado"] == "concluida"
                if args.pilot == "polimento-final":
                    draw_shortcuts(window.screen)
                print(f"Smoke aprovado: {args.pilot}")
                return

            clock = pygame.time.Clock()
            initial_case = args.case or ("vinimuth" if args.pilot == "vitoria" else cases[0])
            index = cases.index(initial_case)
            running = True
            scene = setup(cases[index], folder)
            played = False
            show_shortcuts = args.pilot == "polimento-final" and args.case is None
            while running:
                dt = clock.tick(FPS)
                case = cases[index]
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            break
                        if args.pilot == "polimento-final" and event.key == pygame.K_F1:
                            show_shortcuts = not show_shortcuts
                            continue
                        if case in ("tutorial", "tutorial-vitoria") and event.key == pygame.K_v:
                            audio.stop_all_sfx()
                            scene = setup("tutorial-vitoria", folder)
                            show_shortcuts = False
                            trigger("tutorial-vitoria", scene)
                            played = True
                            continue
                        if case.startswith("mangual") and event.key in (pygame.K_a, pygame.K_s):
                            audio.stop_all_sfx()
                            scene = setup(case, folder)
                            show_shortcuts = False
                            trigger(case, scene, enemy_attack=int(event.key == pygame.K_s))
                            played = True
                            continue
                        numbered = pygame.K_1 <= event.key < pygame.K_1 + min(9, len(cases))
                        if event.key in (pygame.K_r, pygame.K_LEFT, pygame.K_RIGHT) or numbered:
                            if numbered:
                                index = event.key - pygame.K_1
                            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                                index = (index + (1 if event.key == pygame.K_RIGHT else -1)) % len(cases)
                            audio.stop_all_sfx()
                            scene = setup(cases[index], folder)
                            case = cases[index]
                            show_shortcuts = False
                            played = case in DEBUFF_SOUNDS
                            if played:
                                trigger(case, scene, enemy_attack=int(case == "mangual-abalo"))
                            continue
                        if event.key == pygame.K_SPACE and show_shortcuts:
                            show_shortcuts = False
                            continue
                        if (event.key == pygame.K_SPACE and case not in (*CUTSCENE_CASES, "loja")
                                and scenes.current_scene is scene):
                            if not played:
                                trigger(case, scene, enemy_attack=int(case == "mangual-abalo"))
                                played = True
                            continue
                    if not window.handle_window_event(event):
                        if not show_shortcuts:
                            scenes.handle_event(event)
                scenes.update(dt)
                scenes.draw(window.screen)
                label = REVIEW_CASES.get(case, case.title())
                controls = f"{label}  ·  R repetir  ·  Esc sair"
                if len(cases) > 1:
                    controls += (f"  ·  1–{len(cases)} ouvir efeitos" if case in DEBUFF_SOUNDS else
                                 f"  ·  ←/→ escolher teste ({index + 1}/{len(cases)})")
                if case == "loja":
                    controls += "  ·  1 Loja  ·  2 Zanzara  ·  Passe na carta e depois em Comprar"
                elif case == "final-musical":
                    if scenes.current_scene is not scene:
                        controls += "  ·  Espaço avança"
                    elif not played:
                        controls += "  ·  Espaço executa o golpe final"
                    if args.pilot == "loja-epilogo":
                        controls += "  ·  1 Loja  ·  2 Zanzara"
                elif case in ("tutorial", "tutorial-vitoria"):
                    controls += "  ·  Espaço ataque do Slime  ·  V vitória"
                elif case.startswith("mangual"):
                    controls += "  ·  A Varredura  ·  S Abalo"
                elif case in ("golem-plasma", "golem-escudo"):
                    controls += "  ·  1 Plasma  ·  2 Escudo  ·  Espaço executa"
                elif case == "queimadura":
                    controls += "  ·  Espaço encerra o turno e dispara a Queimadura"
                else:
                    controls += "  ·  Espaço avançar" if case in CUTSCENE_CASES else "  ·  Espaço executar"
                if args.pilot == "polimento-final":
                    shortcuts = "   ·   ".join(f"{number} {name}" for number, name in
                                               enumerate(REVIEW_CASES.values(), 1))
                    bar = pygame.Surface((WIDTH, 49), pygame.SRCALPHA)
                    bar.fill((7, 13, 10, 232))
                    window.screen.blit(bar, (0, HEIGHT - 49))
                    draw_text(window.screen, shortcuts, assets.small_font, (209, 176, 108),
                              WIDTH // 2, HEIGHT - 37, center=True)
                    controls += "  ·  F1 legenda"
                draw_text(window.screen, controls, assets.small_font, (240, 224, 184),
                          WIDTH // 2, HEIGHT - 16, center=True)
                if show_shortcuts:
                    draw_shortcuts(window.screen)
                window.present()
    finally:
        audio.shutdown()
        pygame.quit()


if __name__ == "__main__":
    main()
