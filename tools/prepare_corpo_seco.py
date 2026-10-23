"""Pré-processamento dos PNGs originais do Corpo Seco (uso de desenvolvimento).

Os frames atk1/atk3/healer2 foram exportados com o quadriculado de
transparência no RGB e alpha completamente opaco. Este script remove esse
fundo. Deve ser executado a partir do ZIP original do artista; os PNGs
processados já acompanham o jogo e NÃO exigem Pillow/Numpy em produção.

Exemplo:
    python tools/prepare_corpo_seco.py corpo_seco.zip

Dependências exclusivas para pré-processamento: pip install pillow numpy scipy
"""

from pathlib import Path
from io import BytesIO
import argparse
import zipfile


def clean_sprite(image):
    import numpy as np
    from PIL import Image

    image = image.convert("RGBA")
    arr = np.asarray(image).copy()
    rgb = arr[..., :3].astype(np.float32)
    alpha = arr[..., 3].astype(np.float32)

    if np.min(alpha) >= 255:
        # Checkerboard em tons de branco e cinza, sem alpha real.
        channel_min = rgb.min(axis=2)
        neutral = rgb.max(axis=2) - channel_min
        grayness = np.clip((27.0 - neutral) / 16.0, 0, 1)
        bg = np.clip((channel_min - 157.0) / 44.0, 0, 1) * grayness
        alpha = 255.0 * (1.0 - bg)
        alpha[(channel_min > 204) & (neutral < 22)] = 0

        # Elimina franja clara na borda, herdada do quadriculado original.
        # Para pixels semitransparentes, a tonalidade vem do sprite, não
        # do fundo branco. Isso evita um contorno claro ao compor sobre
        # cenários escuros.
        from scipy.ndimage import distance_transform_edt
        solid = alpha >= 244
        if solid.any():
            indices = distance_transform_edt(~solid, return_distances=False, return_indices=True)
            partial = (alpha > 0) & (alpha < 244)
            nearest = rgb[indices[0], indices[1]]
            rgb[partial] = nearest[partial]
    else:
        # PNGs que já eram transparentes têm alpha residual ~=1 fora do corpo.
        alpha[alpha < 16] = 0

    # O alpha muito baixo cria pontinhos claros perceptíveis em fundo escuro.
    alpha[alpha < 42] = 0
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    arr[..., 3] = np.rint(alpha).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_file", type=Path, help="ZIP original do artista")
    parser.add_argument("--output", type=Path, default=Path("assets/corpo_seco"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    with zipfile.ZipFile(args.zip_file) as archive:
        assets = [n for n in archive.namelist()
                  if n.lower().endswith('.png') and Path(n).name.startswith((
                      "idle_", "atk1_", "atk3_", "atk4_", "dano_", "healer2_"))]
        for name in assets:
            image = Image.open(BytesIO(archive.read(name)))
            clean_sprite(image).save(args.output / Path(name).name)
            print("Corrigido:", Path(name).name)


if __name__ == '__main__':
    main()
