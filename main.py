import sys
import pygame

from src.config.settings import TITLE, WIDTH, HEIGHT, FPS
from src.core.window import WindowManager
from src.core.asset_manager import AssetManager
from src.core.scene_manager import SceneManager
from src.core.audio_manager import AudioManager
from src.config.audio_mix import SOUND_VOLUMES
from src.config.music import MUSIC_VOLUME
from src.systems.audio_preferences import AudioPreferences
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
    audio_manager = AudioManager(music_volume=MUSIC_VOLUME)
    audio_manager.register_sounds(
        {
            "ui.click": "ui/click.ogg",
            "ui.confirm": "ui/confirm.ogg",
            "ui.navigate": "ui/navigate.ogg",
            "gameplay.card_hover": "card-place-2.ogg",
            "gameplay.turn_end": "chip-lay-1.ogg",
            "gameplay.ultimate_activate": "ultimate_xamanico_opcao_2.ogg",
            "gameplay.game_over": "game_over_risada_apos_fala_v4.ogg",
            "gameplay.victory": "victory_fanfare_2_curta.ogg",
            "gameplay.attack.punch": "soco_impacto_suave_v2.ogg",
            "gameplay.attack.dagger": "adaga_corte_sangramento.ogg",
            "gameplay.attack.blowgun": "freesound_community-052708_blowgun-39165_sync.ogg",
            "gameplay.attack.arrow_launch": "dennish18-arrow-body-impact-146419_sync.ogg",
            "gameplay.attack.arrow_impact": "flecha_acerto_corporal.ogg",
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
            "gameplay.enemy.acid": "inimigo_acido.ogg",
            "gameplay.enemy.slime": "slime_corpo_fragilizante.ogg",
            "gameplay.enemy.heal": "inimigo_cura.ogg",
            "gameplay.enemy.blade": "inimigo_corte_lamina.ogg",
            "gameplay.boss.zanzara.souls": "zanzara_souls_piloto_v3.ogg",
            "gameplay.boss.zanzara.laugh": "zanzara_laugh_enviada_v5.ogg",
            "gameplay.boss.zanzara.swing": "alvaro_tex_estocada_base_retomada_v6.ogg",
            "gameplay.boss.zanzara.flesh": "alvaro_tex_espada_contato_sangramento_v2.ogg",
            "gameplay.boss.zanzara.smoke": "zanzara_smoke_piloto_v4.ogg",
            "gameplay.boss.zanzara.aura": "zanzara_aura_piloto_v1.ogg",
            "gameplay.boss.zanzara.portal": "zanzara_portal_piloto_v1.ogg",
            "gameplay.boss.zanzara.summon": "zanzara_summon_piloto_v1.ogg",
            "gameplay.boss.zanzara.ferry_hit": "carrasco_execucao_impacto_sangramento_v1.ogg",
            "gameplay.boss.zanzara.ferry": "zanzara_ferry_piloto_v1.ogg",
            "gameplay.boss.guardian.claw": "guardiao_garra_cortante_v4.ogg",
            "gameplay.boss.guardian.claw_hit": "guardiao_garra_sangramento_v4.ogg",
            "gameplay.boss.guardian.stone": "guardiao_pele_rochosa_cauda_v2.ogg",
            "gameplay.boss.guardian.heal": "guardiao_vigor_selvagem_cauda_v2.ogg",
            "gameplay.boss.guardian.roar": "guardiao_rugido_urso_v3.ogg",
            "gameplay.boss.duo.stab": "alvaro_tex_estocada_base_retomada_v6.ogg",
            "gameplay.boss.duo.star": "alvaro_tex_shuriken_giro_v5.ogg",
            "gameplay.boss.duo.whirl": "alvaro_tex_vendaval_espada_combinada_v5.ogg",
            "gameplay.boss.duo.heavy_hit": "alvaro_tex_espada_contato_sangramento_v2.ogg",
            "gameplay.boss.duo.flesh_hit": "alvaro_tex_corte_corporal_contato_v2.ogg",
            "gameplay.boss.duo.smoke": "alvaro_tex_fumaca_inicio_cauda_v3.ogg",
            "gameplay.boss.small.club": "alvaro_tex_pequeno_porrete_movimento_v1.ogg",
            "gameplay.boss.small.body_hit": "alvaro_tex_pequeno_impacto_corporal_v1.ogg",
            "gameplay.boss.small.fury": "alvaro_tex_pequeno_furia_movimento_v1.ogg",
            "gameplay.boss.small.fury_hit": "alvaro_tex_pequeno_furia_impactos_v1.ogg",
            "gameplay.boss.goblin.throw": "goblin_chave_metal_arremesso_v2.ogg",
            "gameplay.boss.goblin.zap": "goblin_descarga_improvisada_v1.ogg",
            "gameplay.boss.goblin.energy_hit": "goblin_laser_queima_sem_repeticao_v4.ogg",
            "gameplay.boss.goblin.toxic": "goblin_acido_jato_corrosao_sincronizado_v6.ogg",
            "gameplay.boss.goblin.retch": "goblin_ansia_final_natural_v7.ogg",
            "gameplay.boss.goblin.shield": "goblin_escudo_runico_v1.ogg",
            "gameplay.boss.goblin.charge": "goblin_sobrecarga_carga_v1.ogg",
            "gameplay.boss.goblin.beam": "goblin_sobrecarga_feixe_v1.ogg",
            "gameplay.boss.gordofera.roar": "gordofera_rugido_tigre_v2.ogg",
            "gameplay.boss.gordofera.guard": "gordofera_guarda_aura_v2.ogg",
            "gameplay.boss.gordofera.jump": "gordofera_salto_impulso_ar_v2.ogg",
            "gameplay.boss.gordofera.tremor": "gordofera_abalo_pedras_fragmentos_v2.ogg",
            "gameplay.boss.corpo.slash": "corpo_seco_corte_movimento_v1.ogg",
            "gameplay.boss.corpo.cross": "corpo_seco_laminas_cruzadas_v1.ogg",
            "gameplay.boss.corpo.spin": "corpo_seco_giro_laminas_v1.ogg",
            "gameplay.boss.corpo.guard": "corpo_seco_postura_defensiva_v1.ogg",
            "gameplay.boss.carrasco.cut": "carrasco_corte_machado_v1.ogg",
            "gameplay.boss.carrasco.sweep": "carrasco_varredura_machado_v1.ogg",
            "gameplay.boss.carrasco.execution": "carrasco_execucao_movimento_v1.ogg",
            "gameplay.boss.carrasco.execution_hit": "carrasco_execucao_impacto_sangramento_v1.ogg",
            "gameplay.boss.carrasco.vigor": "carrasco_vigor_aura_v1.ogg",
        }
    )
    # Ganho por efeito, multiplicado pelos volumes geral, de SFX e da chamada.
    for sound_id, gain in SOUND_VOLUMES.items():
        audio_manager.set_sound_volume(sound_id, gain)
    audio_preferences = AudioPreferences()
    audio_preferences.apply(audio_manager)
    scene_manager = SceneManager(audio_manager=audio_manager, audio_preferences=audio_preferences)
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
