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

    # O jogo abre em janela 1280x720 e renderiza em Full HD (1920x1080).
    # F11 alterna entre tela cheia e a janela 1280x720; F10 alterna a janela
    # entre 1280x720 e o maior tamanho 16:9 que cabe na tela.
    window_manager = WindowManager(WIDTH, HEIGHT, TITLE)
    asset_manager = AssetManager()
    audio_manager = AudioManager()
    audio_manager.register_sounds({
        "ui.click": "ui/click.ogg",
        "ui.confirm": "ui/confirm.ogg",
        "ui.navigate": "ui/navigate.ogg",
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
            # Tela cheia (F11), janela 1280x720 (F10) e redimensionamento valem
            # em qualquer tela, inclusive com modais abertos.
            is_window_shortcut = event.type == pygame.KEYDOWN and event.key in (pygame.K_F11, pygame.K_F10)
            if window_manager.handle_window_event(event):
                if is_window_shortcut:
                    audio_manager.play_sfx("ui.click", volume=1.0)
                continue
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