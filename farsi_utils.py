"""
ابزار کمکی برای نمایش صحیح متن فارسی در Kivy
=================================================
Kivy به‌صورت پیش‌فرض:
    ۱) حروف فارسی/عربی رو به هم نمی‌چسبونه (هر حرف جدا نشون داده می‌شه)
    ۲) جهت متن رو چپ‌به‌راست می‌ذاره (درحالی‌که فارسی راست‌به‌چپه)
    ۳) فونت پیش‌فرضش اصلاً حروف فارسی رو نداره (باکس خالی نشون می‌ده)

این فایل هر سه مشکل رو حل می‌کنه.

نصب کتابخونه‌های لازم (یک‌بار، تو ترمینال):
    pip install arabic-reshaper python-bidi

فونت لازم:
    یه فونت فارسی مثل Vazirmatn دانلود کن:
    https://github.com/rastikerdar/vazirmatn/releases
    فایل .ttf رو بذار تو پوشه‌ی fonts/ کنار همین فایل‌ها
    (مثلاً: project/fonts/Vazirmatn-Medium.ttf)
"""
import os
from kivy.core.text import LabelBase

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RESHAPE_AVAILABLE = True
except ImportError:
    _RESHAPE_AVAILABLE = False
    print("⚠️  کتابخونه‌ی arabic_reshaper یا python-bidi نصب نیست.")
    print("    متن فارسی درست نمایش داده نمی‌شه (حروف بهم نمی‌چسبن و جهتش برعکسه).")
    print("    برای رفعش این دستور رو تو ترمینال بزن:")
    print("    pip install arabic-reshaper python-bidi")

FONT_NAME = "FarsiFont"
_FONT_REGISTERED = False


def lock_font_forever(widget, font_name=FONT_NAME):
    """
    یه نگهبان دائمی روی فونت می‌گذاره: هر لحظه که هر مکانیزمی (KivyMD،
    تایپ کردن، تغییر تم و...) فونت رو عوض کنه، فوراً برمی‌گردونیمش به
    فونت فارسی. برخلاف روش‌های قبلی (تنظیم یه‌بار یا چندبار با تاخیر)،
    این روش برای همیشه فعاله و هیچ باگ تایمینگی نداره.
    """
    def _enforce(instance, value):
        if value != font_name:
            instance.font_name = font_name
    widget.font_name = font_name
    widget.bind(font_name=_enforce)


def set_toolbar_title(toolbar, text):
    """
    عنوان نوار بالا (MDTopAppBar) رو با فونت و شکل درست فارسی تنظیم می‌کنه.
    همیشه به‌جای toolbar.title = "..." از این تابع استفاده کن، وگرنه هم
    حروف بهم نمی‌چسبن، هم فونتش اشتباه می‌مونه.
    """
    from kivy.clock import Clock
    toolbar.title = fa(text)

    def _fix(dt):
        for child in toolbar.walk():
            if hasattr(child, "text") and hasattr(child, "font_name"):
                if child.text == toolbar.title:
                    lock_font_forever(child)
    Clock.schedule_once(_fix, 0)
    Clock.schedule_once(_fix, 0.3)


def register_farsi_font(font_path=None):
    """
    فونت فارسی رو یک‌بار برای کل اپ ثبت می‌کنه.
    این تابع رو باید همون اول کار، قبل از ساخته شدن هر Label/MDLabel صدا بزنی
    (مثلاً تو build() فایل اصلی اپ).

    بعد از ثبت موفق، همه‌جا می‌تونی بنویسی: font_name=FONT_NAME
    """
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return FONT_NAME

    if font_path is None:
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Medium.ttf")

    if not os.path.exists(font_path):
        print(f"⚠️  فایل فونت پیدا نشد: {font_path}")
        print("    فونت Vazirmatn رو دانلود کن و توی پوشه‌ی fonts/ بذار:")
        print("    https://github.com/rastikerdar/vazirmatn/releases")
        return None

    LabelBase.register(name=FONT_NAME, fn_regular=font_path)
    _FONT_REGISTERED = True
    return FONT_NAME


def fa(text):
    """
    متن فارسی رو برای نمایش درست در Kivy آماده می‌کنه (چسبوندن حروف + جهت راست‌به‌چپ).

    همیشه قبل از گذاشتن متن فارسی توی widget.text از این استفاده کن:
        Label(text=fa("سلام دنیا"), font_name=FONT_NAME)

    برای متن انگلیسی خالی هم مشکلی نداره، بدون تغییر برمی‌گرده.
    """
    if not text:
        return text
    if not _RESHAPE_AVAILABLE:
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)