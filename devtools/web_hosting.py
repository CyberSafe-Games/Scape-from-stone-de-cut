"""Auditoria dos limites públicos de hospedagem; não altera os pacotes."""
from pathlib import Path

MIB = 1024 * 1024
SOURCES = {
    "cloudflare": "https://developers.cloudflare.com/pages/platform/limits/",
    "itch": "https://itch.io/docs/creators/html5#zip-file-requirements",
}


def evaluate_files(files):
    """files: pares (caminho relativo, bytes); MB do itch tratado como decimal."""
    files = list(files)
    total = sum(size for _, size in files)
    warnings = []
    def warn(code, message):
        warnings.append({"code": code, "message": message})
    for name, size in files:
        if size > 25 * MIB:
            warn("cloudflare_file", f"{name}: {size / MIB:.2f} MiB excede 25 MiB do Cloudflare Pages.")
        if size > 200_000_000:
            warn("itch_file", f"{name}: excede 200 MB por arquivo no itch.io.")
        if len(name) > 240:
            warn("itch_path", f"{name}: caminho excede 240 caracteres no itch.io.")
    if len(files) > 20_000:
        warn("cloudflare_count", "Mais de 20.000 arquivos: limite do Pages Free excedido.")
    if len(files) > 1_000:
        warn("itch_count", "Mais de 1.000 arquivos no ZIP do itch.io.")
    if total > 500_000_000:
        warn("itch_total", "Conteúdo extraído excede 500 MB no itch.io.")
    return dict(file_count=len(files), total_bytes=total,
                largest_file=max(files, key=lambda row: row[1], default=(None, 0)),
                warnings=warnings, sources=SOURCES, limits_checked="2026-11-25",
                limits=dict(cloudflare_file_bytes=25*MIB, cloudflare_free_files=20_000,
                            itch_file_bytes=200_000_000, itch_files=1_000,
                            itch_total_bytes=500_000_000, itch_path_characters=240),
                note="Pages não publica limite agregado em bytes nesta página; não inventar um teto total.")


def audit_hosting(folder):
    root = Path(folder)
    return evaluate_files((p.relative_to(root).as_posix(), p.stat().st_size)
                          for p in sorted(root.rglob("*")) if p.is_file())
