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
    audio_manager.register_sounds({
        "ui.click": "ui/click.wav",
        "ui.confirm": "ui/confirm.wav",
        "ui.navigate": "ui/navigate.wav",
    })
    scene_manager = SceneManager(audio_manager=audio_manager)
    clock = pygame.time.Clock()

    # Inicializa a aplicação com a cena do Menu Principal
    scene_manager.change_scene(
        MenuScene(scene_manager, window_manager, asset_manager)
    )

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