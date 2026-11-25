#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$HOME/ScapeFromStoneDeCut-android-build"
VENV_DIR="$HOME/.venvs/scape-from-stone-buildozer"
P4A_DIR="$HOME/.buildozer/android/platform/python-for-android"

if [[ ! -f "$SOURCE_DIR/main.py" || ! -f "$SOURCE_DIR/VERSION" ]]; then
    echo "Erro: não encontrei main.py ou VERSION na raiz do projeto." >&2
    exit 1
fi

BUILD_MODE="${1:-debug}"
if [[ "$BUILD_MODE" != "debug" && "$BUILD_MODE" != "release" ]]; then
    echo "Uso: bash android/build_apk.sh [debug|release]" >&2
    exit 2
fi
if [[ "$BUILD_MODE" == "release" ]]; then
    for variable in P4A_RELEASE_KEYSTORE P4A_RELEASE_KEYSTORE_PASSWD P4A_RELEASE_KEYALIAS P4A_RELEASE_KEYALIAS_PASSWD; do
        if [[ -z "${!variable:-}" ]]; then
            echo "Erro: variável $variable não definida. Configure as quatro variáveis de assinatura Android para gerar o APK de release." >&2
            exit 2
        fi
    done
    if [[ ! -f "$P4A_RELEASE_KEYSTORE" ]]; then
        echo "Erro: keystore não encontrado em P4A_RELEASE_KEYSTORE=$P4A_RELEASE_KEYSTORE" >&2
        exit 2
    fi
fi

if ! command -v java >/dev/null 2>&1; then
    echo "Erro: Java 17 não encontrado. Instale openjdk-17-jdk no Ubuntu/WSL." >&2
    exit 1
fi

if [[ ! -x "$VENV_DIR/bin/buildozer" ]]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    "$VENV_DIR/bin/python" -m pip install buildozer setuptools 'Cython==0.29.34'
fi

# Compilar no filesystem Linux evita problemas/perda de desempenho do /mnt/c.
mkdir -p "$BUILD_DIR"
rsync -a \
    --exclude='.git/' \
    --exclude='.idea/' \
    --exclude='build/' \
    --exclude='dist/' \
    --exclude='docs/' \
    --exclude='devtools/' \
    --exclude='tests/' \
    --exclude='saves/' \
    --exclude='installer/' \
    --exclude='android/' \
    --exclude='bin/' \
    --exclude='.buildozer/' \
    --exclude='.venv/' \
    --exclude='venv/' \
    --exclude='_internal/' \
    --exclude='*.exe' \
    "$SOURCE_DIR/" "$BUILD_DIR/"

mkdir -p "$BUILD_DIR/android"
cp "$SCRIPT_DIR/buildozer.spec" "$BUILD_DIR/android/buildozer.spec"

mkdir -p "$(dirname "$P4A_DIR")"
if [[ ! -d "$P4A_DIR/.git" ]]; then
    git clone --depth 1 --branch master \
        https://github.com/kivy/python-for-android.git "$P4A_DIR"
fi

# Point CPython's home at the actual Python bundle. The app root does not
# contain a Python installation, so it cannot be used as config.home.
"$VENV_DIR/bin/python" - "$P4A_DIR/pythonforandroid/bootstraps/common/build/jni/application/src/start.c" "$BUILD_DIR" <<'PY'
from pathlib import Path
import hashlib
import shutil
import sys

start_c = Path(sys.argv[1])
source = start_c.read_text(encoding="utf-8")
source = source.replace("#define P4A_MIN_VER 13", "#define P4A_MIN_VER 11", 1)
if "#define P4A_MIN_VER 11" not in source:
    raise SystemExit("Não reconheci P4A_MIN_VER no bootstrap SDL2.")

dlopen_old = 'PyRun_SimpleString("import io, sys, posix\\n");'
dlopen_new = (
    'PyRun_SimpleString("import io, sys, posix\\n"'
    ' "import os\\nsys.setdlopenflags(os.RTLD_NOW | os.RTLD_GLOBAL)\\n");'
)
if dlopen_new not in source:
    if dlopen_old not in source:
        raise SystemExit("Não reconheci o ponto de configuração de imports do bootstrap SDL2.")
    source = source.replace(dlopen_old, dlopen_new, 1)

global_python_marker = 'dlopen("libpython3.12.so", RTLD_NOW | RTLD_GLOBAL)'
global_python_block = (
    "  void *p4a_python_global = " + global_python_marker + ";\n"
    "  if (p4a_python_global == NULL) {\n"
    "    LOGP(\"Could not promote libpython: %s\", dlerror());\n"
    "  } else {\n"
    "    LOGP(\"libpython promoted to RTLD_GLOBAL\");\n"
    "  }"
)
if global_python_block not in source:
    initialized_marker = '  LOGP("Initialized python");'
    if initialized_marker not in source:
        raise SystemExit("Não reconheci o ponto após inicializar Python no bootstrap SDL2.")
    source = source.replace(
        initialized_marker,
        initialized_marker + "\n\n" + global_python_block,
        1,
    )

config_old = (
    "      PyConfig_InitPythonConfig(&config);\n"
    "      config.program_name = L\"android_python\";"
)
config_new = (
    "      PyConfig_InitPythonConfig(&config);\n"
    "      PyStatus status = PyConfig_SetBytesString(\n"
    "          &config, &config.home, python_bundle_dir);\n"
    "      if (PyStatus_Exception(status)) {\n"
    "        LOGP(\"Failed to set Python home:\");\n"
    "        LOGP(status.err_msg);\n"
    "      }\n"
    "      status = PyConfig_SetBytesString(\n"
    "          &config, &config.program_name, \"android_python\");\n"
    "      if (PyStatus_Exception(status)) {\n"
    "        LOGP(\"Failed to set Python program name:\");\n"
    "        LOGP(status.err_msg);\n"
    "      }"
)
config_previous = config_new.replace(
    "&config, &config.home, python_bundle_dir",
    "&config, &config.home, getenv(\"ANDROID_UNPACK\")",
)
if config_new not in source:
    if config_previous in source:
        source = source.replace(config_previous, config_new, 1)
    elif config_old in source:
        source = source.replace(config_old, config_new, 1)
    else:
        raise SystemExit("Não reconheci a configuração PyConfig do bootstrap SDL2.")

paths_old = (
    "            wchar_t wchar_zip_path[256];\n"
    "            wchar_t wchar_modules_path[256];\n"
    "            swprintf(wchar_zip_path, 256, L\"%s/stdlib.zip\", python_bundle_dir);\n"
    "            swprintf(wchar_modules_path, 256, L\"%s/modules\", python_bundle_dir);\n\n"
    "            config.module_search_paths_set = 1;\n"
    "            PyWideStringList_Append(&config.module_search_paths, wchar_zip_path);\n"
    "            PyWideStringList_Append(&config.module_search_paths, wchar_modules_path);"
)
paths_new = (
    "            char zip_path[512];\n"
    "            char modules_path[512];\n"
    "            snprintf(zip_path, sizeof(zip_path), \"%s/stdlib\", python_bundle_dir);\n"
    "            snprintf(modules_path, sizeof(modules_path), \"%s/modules\", python_bundle_dir);\n"
    "            wchar_t *wchar_zip_path = Py_DecodeLocale(zip_path, NULL);\n"
    "            wchar_t *wchar_modules_path = Py_DecodeLocale(modules_path, NULL);\n"
    "            if (wchar_zip_path == NULL || wchar_modules_path == NULL) {\n"
    "              LOGP(\"Failed to decode Python bundle paths.\");\n"
    "            } else {\n"
    "              config.module_search_paths_set = 1;\n"
    "              status = PyWideStringList_Append(&config.module_search_paths, wchar_zip_path);\n"
    "              if (PyStatus_Exception(status)) LOGP(status.err_msg);\n"
    "              status = PyWideStringList_Append(&config.module_search_paths, wchar_modules_path);\n"
    "              if (PyStatus_Exception(status)) LOGP(status.err_msg);\n"
    "            }\n"
    "            if (wchar_zip_path != NULL) PyMem_RawFree(wchar_zip_path);\n"
    "            if (wchar_modules_path != NULL) PyMem_RawFree(wchar_modules_path);\n"
    "            LOGP(\"Python bundle=%s stdlib=%d modules=%d\", python_bundle_dir,\n"
    "                 dir_exists(zip_path), dir_exists(modules_path));"
)
paths_previous = paths_new.replace("%s/stdlib\",", "%s/stdlib.zip\",").replace(
    "dir_exists(zip_path), dir_exists(modules_path)",
    "file_exists(zip_path), dir_exists(modules_path)",
)
if paths_new not in source:
    if paths_previous in source:
        source = source.replace(paths_previous, paths_new, 1)
    elif paths_old in source:
        source = source.replace(paths_old, paths_new, 1)
    else:
        raise SystemExit("Não reconheci os caminhos PyConfig do bundle Python.")

# Avoid relying on zipimport during CPython's earliest codec initialization.
# Expand the already-built stdlib archive into the bundle and search it as a
# normal directory. This also makes missing stdlib files visible at build time.
recipe_path = Path(sys.argv[1]).parents[6] / "recipes/python3/__init__.py"
recipe_source = recipe_path.read_text(encoding="utf-8")
zip_line = "            shprint(sh.zip, '-X', stdlib_zip, *stdlib_filens)"
expanded_block = (
    zip_line + "\n"
    "\n"
    "        # Android CPython must load encodings before zipimport is ready.\n"
    "        stdlib_dir = join(dirn, 'stdlib')\n"
    "        ensure_dir(stdlib_dir)\n"
    "        import zipfile\n"
    "        with zipfile.ZipFile(stdlib_zip) as archive:\n"
    "            archive.extractall(stdlib_dir)"
)
if expanded_block not in recipe_source:
    if zip_line not in recipe_source:
        raise SystemExit("Não reconheci a montagem do stdlib.zip na recipe Python 3.")
    recipe_path.write_text(recipe_source.replace(zip_line, expanded_block, 1), encoding="utf-8")
    print("Recipe Python Android agora expande stdlib para inicialização segura.")
else:
    print("Recipe Python Android já expande o stdlib.")

# For CPython 3.12, P4A_MIN_VER=13 selects this legacy branch. Py_SetPath
# bypasses the failing PyConfig path calculation; use a safely decoded path.
legacy_old = (
    "            char paths[512];\n"
    "            snprintf(paths, 512, \"%s/stdlib.zip:%s/modules\", python_bundle_dir, python_bundle_dir);\n"
    "            wchar_t *wchar_paths = Py_DecodeLocale(paths, NULL);\n"
    "            Py_SetPath(wchar_paths);"
)
legacy_new = (
    "            char paths[512];\n"
    "            snprintf(paths, sizeof(paths), \"%s/stdlib.zip:%s/modules\", python_bundle_dir, python_bundle_dir);\n"
    "            wchar_t *wchar_paths = Py_DecodeLocale(paths, NULL);\n"
    "            if (wchar_paths == NULL) {\n"
    "              LOGP(\"Failed to decode Python search path.\");\n"
    "            } else {\n"
    "              Py_SetPath(wchar_paths);\n"
    "            }"
)
if legacy_new not in source:
    if legacy_old not in source:
        raise SystemExit("Não reconheci os caminhos legados do bootstrap SDL2.")
    source = source.replace(legacy_old, legacy_new, 1)

init_old = "    PyStatus status = Py_InitializeFromConfig(&config);"
init_new = "    status = Py_InitializeFromConfig(&config);"
if init_old in source:
    source = source.replace(init_old, init_new, 1)
elif init_new not in source:
    raise SystemExit("Não reconheci Py_InitializeFromConfig no bootstrap SDL2.")
start_c.write_text(source, encoding="utf-8")

# p4a can reuse an existing dist after start.c changes. Preserve SDL sources
# and objects, but update start.c and invalidate only its compiled objects.
build_dir = Path(sys.argv[2]).resolve() / "android/.buildozer/android/platform/build-arm64-v8a"
signature = hashlib.sha256(source.encode("utf-8")).hexdigest()
marker = build_dir / ".scape-start-c.sha256"
previous = marker.read_text(encoding="ascii").strip() if marker.exists() else ""
if previous != signature:
    dist = (build_dir / "dists/scapefromstonedecut").resolve()
    assert dist.is_relative_to(build_dir) and dist != build_dir
    if dist.exists():
        shutil.rmtree(dist)
    bootstrap = (build_dir / "build/bootstrap_builds/sdl2").resolve()
    assert bootstrap.is_relative_to(build_dir) and bootstrap != build_dir
    if bootstrap.exists():
        cached_start = bootstrap / "jni/application/src/start.c"
        assert cached_start.resolve().is_relative_to(bootstrap)
        shutil.copy2(start_c, cached_start)
        for relative in (
            "obj/local/arm64-v8a/objs-debug/main/start.o",
            "obj/local/arm64-v8a/libmain.so",
            "libs/arm64-v8a/libmain.so",
        ):
            stale = (bootstrap / relative).resolve()
            assert stale.is_relative_to(bootstrap)
            if stale.exists():
                stale.unlink()
        print("start.o/libmain.so invalidados; fontes SDL preservadas.")
    print("Fonte do bootstrap SDL2 alterada; caches nativos invalidados.")
else:
    print("Fonte do bootstrap SDL2 corresponde à distribuição compilada.")
PY

# Corrige a receita Android do Pygame se a versão instalada ainda omitir as
# fontes SIMD exigidas por surface.so em aparelhos ARM64.
"$VENV_DIR/bin/python" - "$P4A_DIR/pythonforandroid/recipes/pygame/__init__.py" "$BUILD_DIR" <<'PY'
from pathlib import Path
import shutil
import sys

recipe = Path(sys.argv[1])
source = recipe.read_text(encoding="utf-8")
old_version = "version = '2.1.0'"
new_version = "version = '2.6.1'"
if old_version in source:
    recipe.write_text(source.replace(old_version, new_version, 1), encoding="utf-8")
    build_root = Path(sys.argv[2]).resolve()
    pygame_cache = (
        build_root / "android/.buildozer/android/platform/build-arm64-v8a/build/other_builds"
        / "pygame/arm64-v8a__ndk_target_23/pygame"
    ).resolve()
    if pygame_cache.exists():
        assert pygame_cache.is_relative_to(build_root)
        shutil.rmtree(pygame_cache)
    source = recipe.read_text(encoding="utf-8")
    print("Recipe Android fixada em Pygame 2.6.1 (compatível com Python 3.12).")
elif new_version in source:
    print("Recipe Pygame Android já usa a versão 2.6.1.")
else:
    raise SystemExit("Não reconheci a versão da receita Pygame; interrompi o build.")

needle = 'setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()'
patch_line = 'setup_template = setup_template.replace("surface src_c/surface.c", "surface src_c/simd_blitters_sse2.c src_c/simd_blitters_avx2.c src_c/surface.c")'
if patch_line in source:
    print("Receita Pygame já contém as fontes SIMD necessárias.")
elif needle in source:
    recipe.write_text(source.replace(needle, needle + "\n            " + patch_line, 1), encoding="utf-8")
    print("Receita Pygame Android ajustada para ARM64.")
else:
    raise SystemExit("Não reconheci a receita Pygame; interrompi para evitar um APK possivelmente inválido.")

source = recipe.read_text(encoding="utf-8")
pygame_needle = "        env = super().get_recipe_env(arch)\n        env['USE_SDL2'] = '1'"
pygame_marker = "env['CFLAGS'] = env.get('CFLAGS', '') + ' -I' + join(self.ctx.python_recipe.get_build_dir(arch.arch), 'Include', 'cpython')"
if pygame_marker in source:
    print("Recipe Pygame já inclui headers internos do CPython 3.12.")
elif pygame_needle in source:
    replacement = (
        "        env = super().get_recipe_env(arch)\n"
        "        " + pygame_marker + "\n"
        "        env['USE_SDL2'] = '1'")
    recipe.write_text(source.replace(pygame_needle, replacement, 1), encoding="utf-8")
    print("Recipe Pygame ajustado para o layout de headers do CPython 3.12.")
else:
    raise SystemExit("Não reconheci get_recipe_env do Pygame; interrompi o build com segurança.")

depends_old = "depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png']"
depends_new = "depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png', 'cython']"
source = recipe.read_text(encoding="utf-8")
if depends_new in source:
    recipe.write_text(source.replace(depends_new, depends_old, 1), encoding="utf-8")
    print("Recipe Pygame mantida sem a receita Cython incompatível do p4a.")
elif depends_old in source:
    print("Dependências da recipe Pygame verificadas.")
else:
    raise SystemExit("Não reconheci as dependências da receita Pygame; interrompi o build.")

# A receita de Python de destino (não hostpython) também deve ignorar grp.h e
# funções de grupo ausentes no Android; o jogo não usa esses recursos.
python_recipe = recipe.parents[1] / "python3" / "__init__.py"
source = python_recipe.read_text(encoding="utf-8")
needle = "        env = super().get_recipe_env(arch)\n        env['HOSTARCH'] = arch.command_prefix"
patch_line = "        env['ac_cv_header_grp_h'] = 'no'\n        env['ac_cv_func_getgrouplist'] = 'no'\n        env['ac_cv_func_initgroups'] = 'no'\n        env['ac_cv_func_getgrent'] = 'no'\n        env['ac_cv_func_setgrent'] = 'no'\n        env['ac_cv_func_endgrent'] = 'no'"
old_patch_line = "        env['ac_cv_header_grp_h'] = 'no'"
if patch_line in source:
    print("Recipe Python Android já desabilita os recursos grp ausentes no Android.")
elif old_patch_line in source:
    python_recipe.write_text(source.replace(old_patch_line, patch_line, 1), encoding="utf-8")
    print("Recipe Python Android atualizado para desabilitar os símbolos grp ausentes.")
elif needle in source:
    python_recipe.write_text(
        source.replace(needle, "        env = super().get_recipe_env(arch)\n" + patch_line + "\n        env['HOSTARCH'] = arch.command_prefix", 1),
        encoding="utf-8",
    )
    print("Recipe Python Android ajustado sem afetar hostpython.")
else:
    raise SystemExit("Não reconheci a receita Python Android; interrompi o build com segurança.")

prebuild_needle = "    def prebuild_arch(self, arch):\n        super().prebuild_arch(arch)\n        self.ctx.python_recipe = self"
prebuild_marker = "setup_path = join(self.get_build_dir(arch.arch), 'Modules', 'Setup.stdlib.in')"
if prebuild_marker not in source and prebuild_needle in source:
    prebuild_patch = (
        "    def prebuild_arch(self, arch):\n"
        "        super().prebuild_arch(arch)\n"
        "        setup_path = join(self.get_build_dir(arch.arch), 'Modules', 'Setup.stdlib.in')\n"
        "        with open(setup_path, encoding='utf-8') as setup_file:\n"
        "            setup_template = setup_file.read()\n"
        "        grp_line = '@MODULE_GRP_TRUE@grp grpmodule.c'\n"
        "        if grp_line in setup_template:\n"
        "            with open(setup_path, 'w', encoding='utf-8') as setup_file:\n"
        "                setup_file.write(setup_template.replace(grp_line, '#' + grp_line, 1))\n"
        "        elif '#' + grp_line not in setup_template:\n"
        "            raise RuntimeError('Não reconheci a linha grp no Setup.stdlib.in do CPython.')\n"
        "        self.ctx.python_recipe = self"
    )
    python_recipe.write_text(source.replace(prebuild_needle, prebuild_patch, 1), encoding="utf-8")
    print("Recipe Python Android atualizado para omitir grpmodule.")
elif prebuild_marker in source:
    print("Recipe Python Android já omite grpmodule.")
else:
    raise SystemExit("Não reconheci prebuild_arch do recipe Python Android.")
PY

cd "$BUILD_DIR/android"
source "$VENV_DIR/bin/activate"
export PATH="$VENV_DIR/bin:$PATH"
BUILD_LOG="$BUILD_DIR/android/buildozer.log"
if ! APP_P4A_SOURCE_DIR="$P4A_DIR" buildozer android "$BUILD_MODE" >"$BUILD_LOG" 2>&1; then
    if grep -q "You need cython" "$BUILD_LOG"; then
        # pygame 2.6 requires Cython 3 to generate extensions. The upstream
        # p4a cython recipe currently builds target Cython 0.29 and does not
        # provide it to hostpython, so bootstrap it there and retry.
        HOSTPYTHON="$BUILD_DIR/android/.buildozer/android/platform/build-arm64-v8a/build/other_builds/hostpython3/desktop/hostpython3/native-build/root/usr/local/bin/python"
        if [[ ! -x "$HOSTPYTHON" ]]; then
            tail -n 80 "$BUILD_LOG" >&2
            echo "Erro: hostpython não foi gerado para instalar o Cython necessário." >&2
            exit 1
        fi
        "$HOSTPYTHON" -m pip install 'Cython==3.0.11'
        if ! APP_P4A_SOURCE_DIR="$P4A_DIR" buildozer android "$BUILD_MODE" >>"$BUILD_LOG" 2>&1; then
            tail -n 120 "$BUILD_LOG" >&2
            exit 1
        fi
    else
        tail -n 120 "$BUILD_LOG" >&2
        exit 1
    fi
fi

# Android's linker does not expose dependencies of the app library globally.
# CPython extension modules must therefore link directly against libpython.
# The CPython 3.12 configure step in this p4a release omits that dependency.
PYTHON_BUILD_DIR="$(find "$BUILD_DIR/android/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3" -type d -path '*/python3/android-build' -print -quit)"
NDK_LLVM_READELF="$HOME/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf"
if [[ -n "$PYTHON_BUILD_DIR" && -f "$PYTHON_BUILD_DIR/Modules/math.cpython-312.so" ]]; then
    MATH_MODULE="$PYTHON_BUILD_DIR/Modules/math.cpython-312.so"
    if ! "$NDK_LLVM_READELF" -d "$MATH_MODULE" | grep -q 'libpython3.12.so'; then
        find "$PYTHON_BUILD_DIR/Modules" -maxdepth 1 -type f -name '*.cpython-312.so' -delete
        BASE_BLDSHARED="$(sed -n 's/^BLDSHARED=[[:space:]]*//p' "$PYTHON_BUILD_DIR/Makefile" | head -n 1)"
        if [[ -z "$BASE_BLDSHARED" ]]; then
            echo "Erro: não consegui ler BLDSHARED do Makefile do CPython Android." >&2
            exit 1
        fi
        make -C "$PYTHON_BUILD_DIR" sharedmods \
            BLDSHARED="$BASE_BLDSHARED -L$PYTHON_BUILD_DIR -lpython3.12"
        if ! "$NDK_LLVM_READELF" -d "$MATH_MODULE" | grep -q 'libpython3.12.so'; then
            echo "Erro: math.cpython-312.so ainda não está vinculado a libpython3.12.so." >&2
            exit 1
        fi
        "$VENV_DIR/bin/python" - "$BUILD_DIR/android/.buildozer/android/platform/build-arm64-v8a" <<'PY'
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1]).resolve()
dist = (root / "dists/scapefromstonedecut").resolve()
if not dist.is_relative_to(root) or dist == root:
    raise SystemExit("Caminho de distribuição Android fora do build esperado.")
if dist.exists():
    shutil.rmtree(dist)
PY
        if ! APP_P4A_SOURCE_DIR="$P4A_DIR" buildozer android "$BUILD_MODE" >>"$BUILD_LOG" 2>&1; then
            tail -n 120 "$BUILD_LOG" >&2
            exit 1
        fi
    fi
fi

VERSION="$(tr -d '\r\n' < "$BUILD_DIR/VERSION")"
mkdir -p "$SCRIPT_DIR/output"
APK_SOURCE="$(find "$BUILD_DIR/android/bin" -maxdepth 1 -type f -name "*-$BUILD_MODE.apk" -print -quit)"
if [[ -z "$APK_SOURCE" ]]; then
    echo "Erro: o Buildozer terminou sem gerar um APK $BUILD_MODE em $BUILD_DIR/android/bin." >&2
    exit 1
fi
APK_DEST="$SCRIPT_DIR/output/ScapeFromStoneDeCut-$VERSION-$BUILD_MODE.apk"
cp "$APK_SOURCE" "$APK_DEST"
"$VENV_DIR/bin/python" - "$BUILD_DIR/android/.buildozer/android/platform/build-arm64-v8a/.scape-start-c.sha256" "$P4A_DIR/pythonforandroid/bootstraps/common/build/jni/application/src/start.c" <<'PY'
from pathlib import Path
import hashlib
import sys

marker = Path(sys.argv[1])
source = Path(sys.argv[2]).read_bytes()
marker.parent.mkdir(parents=True, exist_ok=True)
marker.write_text(hashlib.sha256(source).hexdigest() + "\n", encoding="ascii")
PY
echo "APK gerado: $APK_DEST"
