"""Importa o ZIP sprites2 como quadros de jogo, sem extrair caminhos do arquivo."""
from io import BytesIO
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from devtools.prepare_boss_eight_frames import silhouette
from devtools.prepare_player_eight_frames import anchor


ASSETS = Path(__file__).resolve().parents[1] / "assets"
PROJECTILES = (
    ("dagger", 2, 2, 96, False), ("fireball", 2, 2, 106, False),
    ("wrench", 1, 4, 76, True), ("arrow", 1, 4, 100, False),
    ("poison_darts", 1, 4, 92, False), ("parasite", 2, 2, 99, True),
    ("spear", 1, 4, 122, False), ("coins", 2, 2, 88, True),
    ("stone_fist", 2, 2, 112, True), ("weakening_potion", 2, 2, 47, False),
    ("poison_potion", 2, 2, 47, False), ("goblin_shot", 1, 4, 100, True),
)
INTENT_ART = (
    ("viniurgo/atk2", "viniurgo/atk1"),
    ("guerreiro_mata/atk1", "guerreiro_mata/atk2"),
    ("lutador/atk1", "lutador/atk2"), ("vinimuth/atk2", "vinimuth/atk1"),
    ("lagarto/atk1", "lagarto/def"), ("esqueleto/atk2", "esqueleto/atk1"),
    ("morcego/atk1", "morcego/atk2"), ("mago/atk1", "mago/atk2"),
    ("macaco/atk1", "macaco/healer2"), ("centauro/atk1", "centauro/atk2"),
    ("golem/atk1", "golem/def"), ("crocodilo/def", "crocodilo/atk1"),
    ("putrefato/atk1", "putrefato/healer2"),
)
PORTRAITS = {
    "alvaro e tex": "alvaro_tex", "gabriel": "carrasco",
    "jose": "goblin_nerd", "jp": "corpo_seco", "manel": "manel",
    "marcus": "zanzara", "otavio": "guardiao", "tex": "tex",
    "tom hanks": "gordofera",
}


def save(image, destination):
    path = ASSETS / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def cells(sheet, columns, rows):
    for row in range(rows):
        for col in range(columns):
            yield sheet.crop((round(col * sheet.width / columns),
                              round(row * sheet.height / rows),
                              round((col + 1) * sheet.width / columns),
                              round((row + 1) * sheet.height / rows)))


def cutout(image, background_floor, keep_lights=True):
    # A malha das folhas JPEG é neutra. A máscara mantém os contornos escuros
    # e os brilhos ligados à silhueta, inclusive nas lâminas metálicas.
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    chroma = np.ptp(rgb, axis=2)
    value = rgb.mean(axis=2)
    core = (chroma > 22) | (value < background_floor)
    mask = Image.fromarray((core * 255).astype("uint8"))
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    near = np.asarray(mask.filter(ImageFilter.MaxFilter(5))) > 0
    alpha = (core & near) | (near & ((chroma > 13) | (keep_lights & (value > 246))))
    result = image.convert("RGBA")
    result.putalpha(Image.fromarray((alpha * 255).astype("uint8")))
    result = silhouette(result)
    return result.crop(result.getbbox())


def dark_bounds(image):
    dark = np.asarray(image.convert("L")) < 86
    ys = np.flatnonzero(dark.sum(axis=1) > image.width * .19)
    xs = np.flatnonzero(dark.sum(axis=0) > image.height * .15)
    return image.crop((xs[0], ys[0], xs[-1] + 1, ys[-1] + 1))


def import_pack(path):
    with ZipFile(path) as archive:
        def images(folder):
            prefix = f"sprites/{folder}/"
            for name in archive.namelist():
                if name.startswith(prefix) and not name.endswith("/"):
                    yield Path(name).stem, Image.open(BytesIO(archive.read(name)))

        for index, (_, sheet) in enumerate(images("arremessaveis")):
            key, columns, rows, width, flip = PROJECTILES[index]
            floor = (102, 98, 94, 75, 93, 211, 100, 205, 211, 91, 79, 91)[index]
            frames = [cutout(cell, floor) for cell in cells(sheet, columns, rows)]
            scale = width / max(frame.width for frame in frames)
            for number, frame in enumerate(frames):
                frame = frame.resize((max(1, round(frame.width * scale)),
                                      max(1, round(frame.height * scale))), Image.Resampling.LANCZOS)
                save(ImageOps.mirror(frame) if flip else frame,
                     f"projectiles/{key}_{number}.png")

        for index, (_, sheet) in enumerate(images("cartas dos inimigos")):
            for key, card in zip(INTENT_ART[index], cells(sheet, 2, 1)):
                art = dark_bounds(card)
                art = art.crop((round(art.width * .06), round(art.height * .05),
                                round(art.width * .94), round(art.height * .55)))
                save(ImageOps.fit(art.convert("RGB"), (144, 135)), f"intent_art/{key}.png")

        icons = ("strength", "energy", "fire", "bleed", "poison", None,
                 "weakness", "shield", "totem")
        for key, (_, sheet) in zip(icons, images("icone de efeito")):
            if key is not None:
                save(ImageOps.fit(dark_bounds(sheet).convert("RGB"), (96, 96)), f"status/{key}.png")

        for name, portrait in images("molduras"):
            save(portrait.convert("RGB").resize((300, 400), Image.Resampling.LANCZOS),
                 f"portraits/source/framed/{PORTRAITS[name]}.png")

        ready = None
        viniurgo = dict(images("viniurgo"))
        for name in ("Retrato", "idle", "atk 1", "atk 2", "tomar dano"):
            sheet = viniurgo[name]
            if name.casefold() == "retrato":
                save(sheet.convert("RGB").resize((300, 400), Image.Resampling.LANCZOS),
                     "portraits/source/framed/viniurgo.png")
                continue
            group = {"atk 1": "atk1", "atk 2": "atk2", "idle": "idle", "tomar dano": "dano"}[name]
            frames = []
            for cell in cells(sheet, 4, 3 if group == "dano" else 2):
                if cell.mode == "RGBA":
                    cell = cell.crop(cell.getbbox())
                else:
                    cell = cutout(cell, 205, keep_lights=False)
                cell = silhouette(cell, particles=False)
                frames.append(ImageOps.mirror(cell.crop(cell.getbbox())))
            if group == "dano":
                frames = [frames[i] for i in (0, 1, 2, 3, 5, 7, 9, 11)]
            scale = 137 / frames[0].height
            for number, frame in enumerate(frames, 1):
                foot_x, floor = anchor(frame)
                frame = frame.resize((round(frame.width * scale), round(frame.height * scale)),
                                     Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", (448, 260))
                canvas.alpha_composite(frame, (round(224 - foot_x * scale), round(258 - floor * scale)))
                canvas.paste((0, 0, 0, 0), (0, 258, 448, 260))
                if group == "idle" and number == 1:
                    ready = canvas
                if number == len(frames) or (number == 1 and group != "idle"):
                    canvas = ready
                save(canvas, f"enemies/eight_frames/viniurgo/{group}_{number}.png")


if __name__ == "__main__":
    import_pack(sys.argv[1])
