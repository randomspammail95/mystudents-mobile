[app]

title = MyStudents
package.name = mystudents
package.domain = org.jean.mystudents

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 

requirements = python3==3.11.8,kivy==2.3.1,kivymd==2.0.0,sqlite3,pillow

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions =
android.api = 34
android.minapi = 21
android.archs = arm64-v8a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
