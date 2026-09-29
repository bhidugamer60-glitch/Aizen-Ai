[app]

title = Aizen AI
package.name = aizenai
package.domain = org.aizen

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 36
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24

android.archs = arm64-v8a,armeabi-v7a

android.accept_sdk_license = True

android.permissions = INTERNET

source.exclude_dirs = .git,.github,bin,build,.buildozer

android.debug_artifact = apk


[buildozer]

log_level = 2
warn_on_root = 1
