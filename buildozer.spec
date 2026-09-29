[app]

# App name
title = Aizen AI

# Package name: only letters/numbers
package.name = aizenai

# Unique package identifier
package.domain = org.aizen

# main.py इसी folder में है
source.dir = .

# App में शामिल files
source.include_exts = py,png,jpg,jpeg,kv,atlas

# Python requirements
requirements = python3,kivy

# App version
version = 1.0

# Orientation
orientation = portrait

# Android settings
fullscreen = 0

# Android API
android.api = 35
android.minapi = 23

# Android architecture
android.archs = arm64-v8a, armeabi-v7a

# Keep build files out of source
source.exclude_dirs = .git,.github,bin,build

# Don't automatically include unnecessary files
exclude_patterns = license,images/*/*.jpg

# Android permissions
android.permissions = INTERNET
