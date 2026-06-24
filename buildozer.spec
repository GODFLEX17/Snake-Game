[app]
title = Snake game
package.name = snakegame
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,ttf,wav,mp3
version = 0.1
requirements = python3,pygame==2.5.2,jnius
orientation = portrait
fullscreen = 1
android.api = 33
android.minapi = 24
android.ndk = 25c
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
p4a.bootstrap = sdl2
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
