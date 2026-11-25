[app]
title = Scape From Stone de Cut
package.name = scapefromstonedecut
package.domain = br.com.cybergames
source.dir = ..
source.include_exts = py,png,ogg,ttf,json
source.exclude_dirs = .git,.idea,build,dist,docs,devtools,tests,saves,installer,android,bin,.buildozer,__pycache__,.venv,venv
version.regex = ^([0-9]+\.[0-9]+\.[0-9]+)$
version.filename = %(source.dir)s/VERSION
orientation = landscape
fullscreen = 1

requirements = python3==3.12.3,hostpython3==3.12.3,pygame
p4a.bootstrap = sdl2
p4a.branch = master
p4a.source_dir =

android.api = 35
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.private_storage = True
android.allow_backup = True
android.debug_artifact = apk
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 0
