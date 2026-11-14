"""Mede todos os efeitos registrados sem reproduzi-los.

Executar na raiz: python devtools/audit_audio_mix.py
Grava docs/audio_mix_audit.json; retorna erro se houver excesso após o ganho.
RMS ativo: blocos de 50 ms a até 20 dB do bloco mais forte, incluindo a cauda.
Não é medição de LUFS, true peak ou avaliação auditiva de distorção.
"""

import array
import ast
import json
import math
import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config.audio_mix import SOUND_VOLUMES


def db(value):
    return round(20 * math.log10(value), 3) if value else -120.0


def main():
    tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    registrations = next(
        ast.literal_eval(node.args[0]) for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register_sounds"
    )
    assert set(registrations) == set(SOUND_VOLUMES)
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    results = []
    try:
        for sound_id, path in registrations.items():
            sound = pygame.mixer.Sound(str(ROOT / "assets/audio" / path))
            samples = array.array("h", sound.get_raw())
            peak = max(map(abs, samples), default=0) / 32768
            blocks = []
            for start in range(0, len(samples), 4410):
                block = samples[start:start + 4410]
                blocks.append(math.sqrt(sum(v * v for v in block) / len(block)) / 32768)
            active = [v for v in blocks if v > 0 and v >= max(blocks, default=0) * 0.1]
            rms = math.sqrt(sum(v * v for v in active) / len(active)) if active else 0
            gain = SOUND_VOLUMES[sound_id]
            # Pygame quantiza o volume para passos de 1/128.
            sound.set_volume(gain)
            applied_gain = sound.get_volume()
            results.append({
                "id": sound_id, "file": path,
                "seconds": round(sound.get_length(), 3), "gain": gain,
                "mixer_gain": applied_gain,
                "source_peak_dbfs": db(peak), "source_active_rms_dbfs": db(rms),
                "source_samples_at_limit": sum(abs(v) >= 32767 for v in samples),
                "output_peak_dbfs": db(peak * applied_gain),
                "output_active_rms_dbfs": db(rms * applied_gain),
            })
    finally:
        pygame.mixer.quit()
    failed = [r["id"] for r in results if r["output_peak_dbfs"] > -9
              or r["output_active_rms_dbfs"] > -22]
    report = {"sample_rate": 44100, "channels": 2,
              "peak_ceiling_dbfs": -9, "active_rms_ceiling_dbfs": -22,
              "scope": "Individual effects at full master/SFX/call volume; excludes channel summation and listening QA",
              "failures": failed, "sounds": results}
    (ROOT / "docs/audio_mix_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Effects: {len(results)}; exceeding limits: {len(failed)}")
    if failed:
        print(failed)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
