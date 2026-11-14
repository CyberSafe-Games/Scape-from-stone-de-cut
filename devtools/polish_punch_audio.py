"""Derivado suave do soco; preserva a origem e não muda a sincronização.

Requer imageio-ffmpeg e numpy somente na preparação. Não restaura informação
perdida por clipping; adeclip é uma estimativa, sujeita à escuta no jogo.
"""
from pathlib import Path
import hashlib
import json
import subprocess

import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/audio/dragon-studio-hard-punch-sfx-515251_sync.ogg'
TARGET = ROOT / 'assets/audio/soco_impacto_suave_v2.ogg'
REPORT = ROOT / 'docs/soco_polimento_v2.json'
FILTERS = ('adeclip=window=55:overlap=75,highpass=f=65,lowpass=f=4800,'
           'afade=t=in:d=0.004,afade=t=out:st=1.17:d=0.12')


def measure(raw):
    data = np.frombuffer(raw, dtype='<f4')
    blocks = [np.sqrt(np.mean(data[i:i+4410].astype('float64') ** 2))
              for i in range(0, len(data), 4410)]
    active = [v for v in blocks if v > 0 and v >= max(blocks) * .1]
    return float(np.max(np.abs(data))), float(np.sqrt(np.mean(np.square(active))))


def main():
    if TARGET.exists() or REPORT.exists():
        raise FileExistsError('Derivado ou relatório já existe; não sobrescrever.')
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    raw = subprocess.run([ffmpeg, '-v', 'error', '-i', str(SOURCE), '-af', FILTERS,
                          '-ar', '44100', '-ac', '2', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    peak, rms = measure(raw)
    # Incorpora a atenuação no derivado; ganho em runtime será 1, sem duplicá-la.
    gain = min(1., 10 ** (-16 / 20) / peak, 10 ** (-28 / 20) / rms)
    subprocess.run([ffmpeg, '-v', 'error', '-n', '-f', 'f32le', '-ar', '44100',
                    '-ac', '2', '-i', '-', '-af', f'volume={gain}',
                    '-c:a', 'libvorbis', '-q:a', '5', str(TARGET)], input=raw, check=True)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == digest
    REPORT.write_text(json.dumps(dict(source=str(SOURCE.relative_to(ROOT)),
        source_sha256=digest, target=str(TARGET.relative_to(ROOT)),
        target_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),
        filters=FILTERS, gain=gain, active_rms_target_dbfs=-28, peak_ceiling_dbfs=-16,
        timing='Sem corte ou mudança de velocidade; preserva a duração e os gatilhos.',
        listening=False, limitation='Atenua aspereza e estima picos; não recupera informação perdida. '
        'Aprovação perceptiva depende da escuta pelo usuário no jogo.'),
        indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
