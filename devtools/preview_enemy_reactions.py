"""Audita reações na arena real, sem saves. Exporta atlas, GIFs e coordenadas."""
import argparse
import json
import os
from pathlib import Path
import sys
import unicodedata
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def slug(name):
    return "".join(c for c in unicodedata.normalize("NFKD", name)
                   if not unicodedata.combining(c)).replace(" · ", "_").replace(" ", "_").lower()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--name", default=None, help="Nome interno ou exibido parcial.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.smoke:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame
    from PIL import Image, ImageDraw
    from unittest.mock import patch
    from src.core.asset_manager import AssetManager
    from src.core.window import WindowManager
    from src.core.scene_manager import SceneManager
    from src.scenes.battle_scene import BattleScene
    from src.systems.enemy_factory import (create_point_enemy, create_alvaro_tex, create_road_enemy,
                                           create_enemy, ENEMY_TYPES, MINIBOSS_TYPES, choose_enemy_intent)
    from src.systems.normal_enemy_catalog import BIOME_ENEMIES
    from src.config.boss_names import boss_display_name
    from src.config.layout import ENEMY_X, PLAYER_GROUND_Y, FLASH_DURATION
    from src.ui.enemy_reactions import support, prepare_hurt, calm_idle_frames
    from src.ui import zanzara_necromancer as zanzara
    pygame.init()
    window, assets = WindowManager(), AssetManager()
    enemies = [(level, create_point_enemy(level)) for level in range(1, 8)]
    enemies.append((2, create_alvaro_tex(2, phase=2)))
    for level, names in BIOME_ENEMIES.items():
        for name in names:
            with patch("src.systems.enemy_factory.random.choice", return_value=name):
                enemies.append((level, create_road_enemy(level)))
    for mini, pool in ((False, ENEMY_TYPES), (True, MINIBOSS_TYPES)):
        for entry in pool:
            if any(e.name == entry[0] for _, e in enemies):
                continue
            with patch("src.systems.enemy_factory.random.choice", return_value=entry):
                enemies.append((3, create_enemy(3, is_miniboss=mini)))
    if args.name:
        enemies = [(level,e) for level,e in enemies if args.name.lower() in
                   (e.name+" "+boss_display_name(e.name)).lower()]
    args.output.mkdir(parents=True, exist_ok=True)
    atlas = Image.new("RGB", (1600, len(enemies)*175), "#14261f")
    labels = ImageDraw.Draw(atlas)
    records = {}
    for row, (level, enemy) in enumerate(enemies):
        scene = BattleScene(SceneManager(), window, assets, selected_level=level)
        scene.boss_dialogue = None
        scene._boss_events = []
        scene.engine.enemy = enemy
        scene.engine.player.hp = scene.engine.player.max_hp = 999
        choose_enemy_intent(enemy)
        view = scene.entity_view
        view.enemy_idle_timer = 725
        ready = view.get_enemy_frame(enemy, interpolate=True)
        frames = assets.get_enemy_sprite_group(enemy.name, "dano")
        dedicated = enemy.name.lower() == "zanzara" and zanzara.available()
        if dedicated:
            ready, frames = zanzara.reaction_ready(), zanzara.state_frames("dano")
        audit = prepare_hurt(tuple(frames), ready)[1] if ready else ()
        record = dict(display=boss_display_name(enemy.name), level=level,
                      renderer="necromante" if dedicated else "sprite" if ready else "procedural",
                      frames=list(audit), duration_ms=FLASH_DURATION, world_samples=[])
        images = []
        for i, elapsed in enumerate((0, 65, 120, 190, 300, 420, 520, 560)):
            view.enemy_flash = FLASH_DURATION-elapsed
            actor = pygame.Surface((1920,1080), pygame.SRCALPHA)
            view.draw_enemy(actor, enemy)
            cx, floor, box = support(actor)
            record["world_samples"].append(dict(ms=elapsed, x=cx, floor=floor, bbox=list(box)))
            scene.draw(window.screen)
            crop = pygame.Rect(ENEMY_X-230, PLAYER_GROUND_Y-320, 460, 340)
            image = Image.frombytes("RGB", crop.size, pygame.image.tobytes(window.screen.subsurface(crop), "RGB"))
            ImageDraw.Draw(image).text((8,8),f"{record['display']} / {elapsed} ms",fill="white")
            images.append(image)
            thumb = image.resize((200,148), Image.Resampling.LANCZOS)
            atlas.paste(thumb,(i*200,row*175+25))
        labels.text((6,row*175+4),record["display"],fill="white")
        images[0].save(args.output/(slug(enemy.name)+"_hurt.gif"),save_all=True,
                       append_images=images[1:],duration=[65,55,70,110,120,100,40,450],loop=0)
        records[enemy.name] = record
        print(enemy.name,":",sum(r["accepted"] for r in audit),"/",len(audit),"poses estáveis; arena OK",flush=True)
        if not args.smoke:
            clock = pygame.time.Clock()
            for _ in range(2):
                for elapsed in range(0, FLASH_DURATION+450, 16):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            pygame.quit()
                            return
                    view.enemy_flash = max(0, FLASH_DURATION-elapsed)
                    scene.draw(window.screen)
                    window.present()
                    clock.tick(60)
    atlas.save(args.output/"reacoes_arena.png")
    if any(e.name == "Goblin Nerd" for _,e in enemies):
        idle = assets.get_enemy_sprite_group("Goblin Nerd", "idle")
        poses = calm_idle_frames(idle[0])
        movie = []
        from src.ui.enemy_reactions import JOZEPHINO_IDLE_ORDER
        for index in JOZEPHINO_IDLE_ORDER:
            frame = poses[index]
            im = Image.frombytes("RGBA", frame.get_size(), pygame.image.tobytes(frame,"RGBA"))
            canvas = Image.new("RGB",(240,230),"#14261f")
            cut = im.crop((150,170,310,320)).resize((208,195),Image.Resampling.NEAREST)
            canvas.paste(cut,(16,25),cut)
            movie.append(canvas)
        movie[0].save(args.output/"jozephino_idle.gif",save_all=True,append_images=movie[1:],duration=160,loop=0)
    (args.output/"coordenadas.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Conferência concluída: {len(records)} formas, sem saves reais.")
    pygame.quit()


if __name__ == "__main__":
    main()
