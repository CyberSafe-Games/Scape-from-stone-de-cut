import sys
import pygame

from src.config.settings import TITLE, WIDTH, HEIGHT, FPS
from src.core.window import WindowManager
from src.core.asset_manager import AssetManager
from src.core.scene_manager import SceneManager
from src.core.audio_manager import AudioManager
from src.scenes.menu_scene import MenuScene


def main():
    """Ponto de entrada principal da aplicação.

    Inicializa o motor Pygame, os gerenciadores centrais e executa o ciclo de vida do jogo.
    """
    pygame.init()

    window_manager = WindowManager(WIDTH, HEIGHT, TITLE)
    asset_manager = AssetManager()
    audio_manager = AudioManager()
    audio_manager.register_sounds(
        {
            "ui.click": "ui/click.ogg",
            "ui.confirm": "ui/confirm.ogg",
            "ui.navigate": "ui/navigate.ogg",
            "gameplay.card_hover": "card-place-2.ogg",
            "gameplay.turn_end": "chip-lay-1.ogg",
            "gameplay.ultimate_activate": "ultimate_xamanico_opcao_2.ogg",
            "gameplay.game_over": "game_over_fogueira_sombria_v2.ogg",
            "gameplay.victory": "victory_fanfare_2_curta.ogg",
            "gameplay.attack.punch": "dragon-studio-hard-punch-sfx-515251_sync.ogg",
            "gameplay.attack.dagger": "adaga_corte_sangramento.ogg",
            "gameplay.attack.blowgun": "freesound_community-052708_blowgun-39165_sync.ogg",
            "gameplay.attack.arrow_impact": "dennish18-arrow-body-impact-146419_sync.ogg",
            "gameplay.attack.charge": "investida_passos_isolados.ogg",
            "gameplay.attack.charge_impact": "investida_impacto_corporal.ogg",
            "gameplay.attack.spear": "lanca_perfurante_sync_v2.ogg",
            "gameplay.attack.twin_axes": "machados_gemeos_sync_v2.ogg",
            "gameplay.attack.shield_break": "machado_quebra_madeira.ogg",
            "gameplay.attack.fireball": "bola_de_fogo_continua.ogg",
            "gameplay.skill.aura": "aura_rubra_sync_v2.ogg",
            "gameplay.skill.shield_light": "esfera_protetora_leve_curta.ogg",
            "gameplay.skill.shield_heavy": "esfera_escudo_v2_continuacao_natural.ogg",
            "gameplay.skill.totem": "totem_protecao_sync_v2.ogg",
            "gameplay.potion.heal": "pocao_cura_sync.ogg",
            "gameplay.potion.cleanse": "pocao_purificadora_sync.ogg",
            "gameplay.potion.poison": "pocao_venenosa_corrosao.ogg",
            "gameplay.potion.weaken": "pocao_fragilizante_composta.ogg",
            "gameplay.skill.dispel": "amuleto_dissipador_ativacao.ogg",
            "gameplay.skill.mask": "mascara_ancestral_canto_curto.ogg",
            "gameplay.skill.energy": "surto_energia_continuacao_curta.ogg",
        }
    )
    scene_manager = SceneManager(audio_manager=audio_manager)
    clock = pygame.time.Clock()

    # Inicializa a aplicação com a cena do Menu Principal
    scene_manager.change_scene(MenuScene(scene_manager, window_manager, asset_manager))

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            scene_manager.handle_event(event)

        scene_manager.update(dt)

        # Renderiza a cena atual na resolução virtual fixa e apresenta com escala adaptativa
        scene_manager.draw(window_manager.virtual_screen)
        window_manager.present()

    # Persiste o checkpoint também quando a janela é fechada diretamente.
    active_scene = scene_manager.current_scene
    if hasattr(active_scene, "save_on_exit"):
        active_scene.save_on_exit()

    audio_manager.shutdown()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
