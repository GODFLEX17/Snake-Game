[app]
title = Snake Game Adventure
package.name = snakegame
package.domain = org.godflex17
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 0.1
requirements = python3,kivy==2.3.0,pygame,pillow

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 24
android.ndk = 25c
android.archs = armeabi-v7a, arm64-v8a
p4a.branch = master

[buildozer]
log_level = 1
warn_on_root = 1
