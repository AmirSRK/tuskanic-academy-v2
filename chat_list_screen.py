from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from farsi_utils import fa, FONT_NAME, set_toolbar_title, lock_font_forever
from chat_theme import get_colors, ACCENT, ACCENT_SOFT, TEXT_ON_ACCENT
from kivy.clock import Clock

ROW_HEIGHT = dp(74)
AVATAR_SIZE = dp(48)
DIVIDER_HEIGHT = dp(1)

# رنگ‌های مختلف برای آواتار هر مخاطب (مثل تلگرام)، بر اساس اسم انتخاب می‌شه
AVATAR_PALETTE = [
    (0.122, 0.373, 0.290, 1.0),   # #1F5F4A  (سبز تیره - اصلی)
    (0.831, 0.659, 0.263, 1.0),   # #D4A843  (طلایی/خاکی - مکمل)
    (0.910, 0.835, 0.718, 1.0),   # #E8D5B7  (کرم/بژ - روشن)
    (0.357, 0.290, 0.549, 1.0),   # #5B4A8C  (بنفش مایل به آبی)
    (0.769, 0.451, 0.227, 1.0),   # #C4733A  (نارنجی سوخته - مکمل سبز),   # سبز تیره
]

def _avatar_color(name):
    return AVATAR_PALETTE[sum(ord(ch) for ch in name) % len(AVATAR_PALETTE)]


def _truncate(text, max_chars=42):
    """
    کوتاه‌کردن متن با شمردن مستقیم تعداد حرف (نه ویژگی shorten خودِ
    Kivy که وابسته به عرض واقعی رندرشده‌ست و گاهی قبل از تکمیل layout
    اجرا می‌شه و متن رو به یه حرف تنها کوتاه می‌کنه). این روش قطعی و
    همیشه درسته.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _fixed_label(text, width, height, **kwargs):
    """لیبل با عرض/ارتفاع دقیقاً مشخص، بدون وابستگی به texture_size."""
    label = MDLabel(
        text=text,
        size_hint=(None, None),
        width=width,
        height=height,
        text_size=(width, height),
        valign="middle",
        **kwargs,
    )
    lock_font_forever(label)
    return label


def _responsive_label(text, height, **kwargs):
    """
    لیبل تک‌خطی که عرضش خودکار با فضای باقی‌مونده‌ی والدش پر می‌شه (نه
    یه عدد ثابت) - چون تک‌خطیه (نه چندخطی راست‌به‌چپ)، هیچ خطر بهم‌ریختن
    ترتیب نداره، فقط باید عرض واقعی صفحه رو درست دنبال کنه.
    """
    label = MDLabel(
        text=text,
        size_hint=(1, None),
        height=height,
        valign="middle",
        **kwargs,
    )
    label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, height)))
    lock_font_forever(label)
    return label


class ChatListScreen(MDScreen):
    name = "chat_list"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = MDApp.get_running_app()
        if app:
            app.theme_cls.bind(theme_style=self._on_theme_change)
        self.build_chat_list()

    def build_chat_list(self):
        c = get_colors()
        self.layout = MDBoxLayout(orientation="vertical", md_bg_color=c["BACKGROUND"])

        # ---------- هدر ----------
        self.toolbar = MDTopAppBar()
        set_toolbar_title(self.toolbar, "پیام‌ها")
        self.toolbar.left_action_items = [["arrow-left", lambda x: self.go_back()]]
        self.toolbar.md_bg_color = ACCENT
        self.toolbar.specific_text_color = TEXT_ON_ACCENT
        self.toolbar.elevation = 2
        self.layout.add_widget(self.toolbar)

        # ---------- لیست چت‌ها ----------
        scroll = ScrollView(bar_width=0, do_scroll_x=False)
        self.list_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            md_bg_color=c["BACKGROUND"],
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))

        chats = [
            {"name": "گروه پایتون", "last_message": "جلسه فردا ساعت ۴ برگزار می‌شه", "time": "12:30"},
            {"name": "پشتیبانی", "last_message": "مشکلت حل شد؟", "time": "10:15"},
            {"name": "دوره جاوا", "last_message": "تمرین جدید آپلود شد، حتماً ببینید", "time": "09:00"},
            {"name": "دوست قدیمی", "last_message": "سلام! چطوری؟ خیلی وقته ندیدمت", "time": "دیروز"},
        ]

        for i, chat in enumerate(chats):
            is_last = i == len(chats) - 1
            item = self.create_chat_item(chat["name"], chat["last_message"], chat["time"], is_last)
            self.list_layout.add_widget(item)

        scroll.add_widget(self.list_layout)
        self.layout.add_widget(scroll)

        Clock.schedule_once(lambda dt: self.add_widget(self.layout) ,0.1)

    # ==================================================
    # دارک‌مود
    # ==================================================
    def _on_theme_change(self, *args):
        c = get_colors()
        self.layout.md_bg_color = c["BACKGROUND"]
        self.list_layout.md_bg_color = c["BACKGROUND"]

    # ==================================================
    # آیتم لیست چت (سبک تلگرام: بدون کارت جداگانه، فقط یه خط جداکننده)
    # ==================================================
    def create_chat_item(self, name, last_message, time, is_last=False):
        c = get_colors()
        outer = MDBoxLayout(orientation="vertical", size_hint_y=None, height=ROW_HEIGHT)

        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=ROW_HEIGHT - (0 if is_last else DIVIDER_HEIGHT),
            padding=["14dp", "10dp", "14dp", "10dp"],
            spacing="12dp",
        )
        row.bind(on_touch_down=lambda inst, touch, n=name: self.open_chat(inst, touch, n))

        # ---------- آواتار دایره‌ای رنگی ----------
        avatar_color = _avatar_color(name)
        avatar = Widget(size_hint=(None, None), size=(AVATAR_SIZE, AVATAR_SIZE))
        with avatar.canvas.before:
            Color(*avatar_color)
            avatar.ellipse = Ellipse(pos=avatar.pos, size=avatar.size)
        avatar.bind(pos=self._redraw_avatar, size=self._redraw_avatar)
        avatar._avatar_color = avatar_color

        letter = _fixed_label(
            fa(name[0].upper()),
            width=AVATAR_SIZE,
            height=AVATAR_SIZE,
            font_name=FONT_NAME,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            bold=True,
            font_size="18sp",
            halign="center",
        )
        avatar.add_widget(letter)

        avatar_holder = MDBoxLayout(size_hint_x=None, width=AVATAR_SIZE)
        avatar_holder.add_widget(avatar)

        # ---------- ستون متن: (اسم + ساعت) بالا، پیام آخر پایین ----------
        text_col = MDBoxLayout(orientation="vertical", spacing="4dp")

        top_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        time_label = _fixed_label(
            fa(time) if any("\u0600" <= ch <= "\u06FF" for ch in time) else time,
            width=dp(56),
            height=dp(20),
            font_name=FONT_NAME,
            theme_text_color="Custom",
            text_color=c["TEXT_MUTED"],
            font_size="11sp",
            halign="left",
        )
        name_label = _responsive_label(
            fa(name),
            height=dp(22),
            font_name=FONT_NAME,
            theme_text_color="Custom",
            text_color=c["TEXT_DARK"],
            bold=True,
            font_size="16sp",
            halign="right",
        )
        top_row.add_widget(time_label)
        top_row.add_widget(name_label)
        text_col.add_widget(top_row)

        last_label = _responsive_label(
            fa(_truncate(last_message)),
            height=dp(20),
            font_name=FONT_NAME,
            theme_text_color="Custom",
            text_color=c["TEXT_MUTED"],
            font_size="13sp",
            halign="right",
        )
        text_col.add_widget(last_label)

        # ترتیب راست‌به‌چپ: متن (سمت چپ‌تر) - آواتار (راست‌ترین)
        row.add_widget(text_col)
        row.add_widget(avatar_holder)

        outer.add_widget(row)

        if not is_last:
            divider = Widget(size_hint_y=None, height=DIVIDER_HEIGHT)
            with divider.canvas:
                Color(*c["DIVIDER"])
                divider.rect = Rectangle(pos=divider.pos, size=divider.size)
            divider.bind(
                pos=lambda inst, val: setattr(inst.rect, "pos", val),
                size=lambda inst, val: setattr(inst.rect, "size", val),
            )
            outer.add_widget(divider)

        return outer

    def _redraw_avatar(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*instance._avatar_color)
            instance.ellipse = Ellipse(pos=instance.pos, size=instance.size)

    def open_chat(self, instance, touch, name):
        if instance.collide_point(*touch.pos):
            app = MDApp.get_running_app()
            chat_screen = self.manager.get_screen("chat")
            set_toolbar_title(chat_screen.toolbar, name)
            if app:
                app.go_to("chat")
            else:
                self.manager.current = "chat"

    def go_back(self):
        app = MDApp.get_running_app()
        if app:
            app.go_back()
        else:
            self.manager.current = "main"