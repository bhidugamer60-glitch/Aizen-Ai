[app]

title = Aizen AI
package.name = aizenai
package.domain = org.aizen

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0.0

# Pinned versions (latest p4a master builds Python 3.14 which breaks)
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24

android.archs = arm64-v8a,armeabi-v7a

android.accept_sdk_license = True

android.permissions = INTERNET

source.exclude_dirs = .git,.github,bin,build,.buildozer

android.debug_artifact = apk

# Stable python-for-android release instead of master
p4a.branch = v2024.01.21


[buildozer]

log_level = 2
warn_on_root = 1
