"""Prévia manual do piloto com animações e fila de áudio reais; não usa saves.

1: garras; 2: pedra; 3: cura; 4: Ultimate; Esc: sair.
--smoke percorre as quatro ações com áudio/vídeo dummy, sem abrir janela.
--duo mostra a primeira fase de Álvaro e Tex (1 estocada, 2 estrela, 3 fumaça, 4 Ultimate).
--small mostra a segunda fase (1 chute, 2 porrete, 3 shuriken, 4 Fúria).
--goblin mostra Goblin Nerd (1 chave, 2 descarga, 3 tóxico, 4 escudo, 5 Ultimate).
--gordofera mostra Gordofera (1 garras, 2 rugido, 3 cabeçada, 4 guarda, 5 Abalo).
--corpo mostra Corpo Seco (1 corte, 2 cruzadas, 3 defesa, 4 giratório).
--carrasco mostra Carrasco (1 corte, 2 varredura, 3 vigor, 4 execução).
"""
import ast
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if "--smoke" in sys.argv:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from src.config.audio_mix import SOUND_VOLUMES
from src.core.audio_manager import AudioManager
from src.core.asset_manager import AssetManager
from src.core.scene_manager import SceneManager
from src.core.window import WindowManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_guardiao_da_pedra, create_alvaro_tex, create_goblin_nerd, create_gordofera, create_corpo_seco, create_carrasco_da_vigilia, create_zanzara


def main():
    pygame.init()
    zanzara = "--zanzara" in sys.argv
    duo = "--duo" in sys.argv
    small = "--small" in sys.argv
    goblin = "--goblin" in sys.argv
    gordofera = "--gordofera" in sys.argv
    corpo = "--corpo" in sys.argv
    carrasco = "--carrasco" in sys.argv
    count = 5 if goblin or gordofera else 4
    title = "Zanzara" if zanzara else "Carrasco da Vigília" if carrasco else "Corpo Seco" if corpo else "Gordofera" if gordofera else "Goblin Nerd" if goblin else "Álvaro e Tex — Pequeno, fase 2" if small else "Álvaro e Tex — fase 1" if duo else "Guardião da Pedra"
    window = WindowManager(title=f"{title} — piloto de áudio | teclas 1 a {count}")
    assets = AssetManager()
    audio = AudioManager()
    tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    sounds = next(ast.literal_eval(n.args[0]) for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "register_sounds")
    audio.register_sounds(sounds)
    for sound_id, gain in SOUND_VOLUMES.items():
        audio.set_sound_volume(sound_id, gain)
    manager = SceneManager(audio_manager=audio)

    def start(choice):
        audio.stop_all_sfx()
        scene = BattleScene(manager, window, assets, selected_level=7 if zanzara else 1)
        scene.engine.enemy = create_zanzara() if zanzara else create_carrasco_da_vigilia() if carrasco else create_corpo_seco() if corpo else create_gordofera() if gordofera else create_goblin_nerd() if goblin else create_alvaro_tex(phase=2) if small else create_alvaro_tex(phase=1) if duo else create_guardiao_da_pedra()
        scene.engine.state = "player_turn"
        if zanzara and choice in (1, 2, 3, 4):
            scene._handle_combat_event("attack", attacker="enemy", action={1:"atk1",2:"atk2",3:"atk3",4:"atk3"}[choice], ultimate=choice == 4)
            scene._handle_combat_event("flash", target="player")
        elif carrasco and choice in (1, 2, 4):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action={1: "atk1", 2: "atk2", 4: "atk3"}[choice], ultimate=choice == 4)
            scene._handle_combat_event("flash", target="player")
        elif carrasco and choice == 3:
            scene._handle_combat_event("enemy_action", action="healer2")
        elif corpo and choice in (1, 2, 4):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action={1: "atk1", 2: "atk3", 4: "atk4"}[choice], ultimate=choice == 4)
            scene._handle_combat_event("flash", target="player")
        elif corpo and choice == 3:
            scene._handle_combat_event("enemy_action", action="def")
        elif gordofera and choice in (1, 2, 3, 5):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action={1: "atk1", 2: "atk2", 3: "atk3", 5: "atk4"}[choice], ultimate=choice == 5)
            scene._handle_combat_event("flash", target="player")
        elif gordofera and choice == 4:
            scene._handle_combat_event("enemy_action", action="def")
        elif goblin and choice in (1, 2, 3, 5):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action={1: "atk1", 2: "atk2", 3: "atk3", 5: "atk2"}[choice], ultimate=choice == 5)
            scene._handle_combat_event("flash", target="player")
        elif goblin and choice == 4:
            scene._handle_combat_event("enemy_action", action="healer2")
        elif small and choice in (1, 2, 3, 4):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action={1: "atk1", 2: "atk2", 3: "atk4", 4: "atk3"}[choice], ultimate=choice == 4)
            scene._handle_combat_event("flash", target="player")
        elif duo and choice in (1, 2, 4):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action={1: "atk1", 2: "atk2", 4: "atk4"}[choice], ultimate=choice == 4)
            scene._handle_combat_event("flash", target="player")
        elif duo and choice == 3:
            scene._handle_combat_event("enemy_action", action="healer2")
        elif choice in (1, 4):
            scene._handle_combat_event("attack", attacker="enemy",
                                      action="atk1" if choice == 1 else "atk2", ultimate=choice == 4)
            scene._handle_combat_event("flash", target="player")
        elif choice in (2, 3):
            scene._handle_combat_event("enemy_action", action="def" if choice == 2 else "healer2")
        return scene

    if "--smoke" in sys.argv:
        for choice in range(1, count + 1):
            scene = start(choice)
            for _ in range(200):
                scene.update(16)
            scene.draw(window.screen)
        print(f"{count} ações percorridas e renderizadas; sem avaliação auditiva.")
    else:
        scene = start(0)
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif zanzara and event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                    scene = start(0)
                    scene.engine.player.hp = 0
                    scene.engine.state = "game_over"
                    scene._handle_combat_event("game_over")
                elif zanzara and event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                    scene = start(0)
                    scene._handle_combat_event("attack", attacker="player", action="Soco Simples")
                    scene._handle_combat_event("flash", target="enemy")
                elif event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_0 + count:
                    scene = start(event.key - pygame.K_0)
                else:
                    window.handle_window_event(event)
            scene.update(dt)
            scene.draw(window.screen)
            caption = assets.small_font.render(
                ("ZANZARA | 1 Foice Sombria | 2 Passo | 3 Grilhoes | 4 Travessia | H Receber golpe | G Game Over | Esc Sair" if zanzara else
                 "CARRASCO | 1 Corte | 2 Varredura | 3 Vigor | 4 Execução | Esc Sair" if carrasco else
                 "CORPO SECO | 1 Corte | 2 Cruzadas | 3 Defesa | 4 Giratório | Esc Sair" if corpo else
                 "GORDOFERA | 1 Garras | 2 Rugido | 3 Cabeçada | 4 Guarda | 5 Abalo | Esc Sair" if gordofera else
                 "GOBLIN | 1 Chave | 2 Descarga | 3 Tóxico | 4 Escudo | 5 Sobrecarga | Esc Sair" if goblin else
                 "FASE 2 | 1 Chute | 2 Porrete | 3 Shuriken | 4 Fúria | Esc Sair" if small else
                 "FASE 1 | 1 Estocada | 2 Estrela | 3 Fumaça | 4 Vendaval | Esc Sair" if duo else
                 "PILOTO | 1 Garras | 2 Pele Rochosa | 3 Vigor Selvagem | 4 Rugido | Esc Sair"), True, (255, 235, 180))
            window.screen.blit(caption, (40, 190))
            pygame.transform.smoothscale(window.screen, window.display_surface.get_size(), window.display_surface)
            pygame.display.flip()
    audio.shutdown()
    pygame.quit()


if __name__ == "__main__":
    main()
