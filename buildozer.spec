[app]

# ------------------------------------------------------------------
# اطلاعات پایه‌ی اپ
# ------------------------------------------------------------------
title = Tuskanic Academy
package.name = tuskanicacademy
package.domain = org.tuskanic

source.dir = .
source.main = TUSKANIC_Academy-7.py
source.include_exts = py,png,jpg,jpg,kv,atlas,ttf,json

version = 1.0.0

# ------------------------------------------------------------------
# کتابخانه‌های مورد نیاز (نسخه‌ها ثابت شدن تا بیلد هر بار یکسان و
# قابل پیش‌بینی باشه و با آپدیت ناگهانی kivy/kivymd خراب نشه)
# ------------------------------------------------------------------
requirements = python3==3.11.6,hostpython3==3.11.6,kivy==2.3.0,kivymd==1.2.0,pyjnius,pillow

orientation = all
fullscreen = 0

# ------------------------------------------------------------------
# دسترسی‌ها: اینترنت + وضعیت شبکه (برای بنر آفلاین/آنلاین اپ)
# ------------------------------------------------------------------
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

# ------------------------------------------------------------------
# API بالا = پشتیبانی از رفرش‌ریت‌های بالا (90/120/144هرتز) روی
# گوشی‌هایی که ازش پشتیبانی می‌کنن. minapi پایین = سازگاری با
# گوشی‌های قدیمی‌تر هم (اندروید 5+).
# ------------------------------------------------------------------
android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True
android.presplash_color = #5B2EFF

# آیکون اپ - فایل icon.png باید توی ریشه‌ی همین ریپازیتوری باشه
icon.filename = %(source.dir)s/icon.png

# به‌جای لوگوی پیش‌فرض Kivy، موقع باز شدن اپ همون آیکون خودمون نشون داده بشه
presplash.filename = %(source.dir)s/icon.png

# استارت سریع‌تر: کدها به‌صورت pyc کامپایل میشن و چیزی اضافه‌بار نمی‌گیریم
android.release_artifact = apk

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
