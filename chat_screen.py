from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.app import MDApp
from datetime import datetime
from kivy.clock import Clock
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivy.animation import Animation
from kivymd.uix.screen import MDScreen
from farsi_utils import fa, FONT_NAME, set_toolbar_title, lock_font_forever
from chat_theme import get_colors, ACCENT, ACCENT_GREEN, BUBBLE_USER, TEXT_ON_ACCENT

# تلاش برای بهتر شدن رفتار کیبورد روی گوشی
try:
    Window.softinput_mode = "below_target"
except Exception:
    pass

# ---------- عدد‌های ثابت (عمداً ثابت، نه بر اساس عرض پنجره، تا رفتار
# همیشه یکسان و قابل‌پیش‌بینی باشه، هم روی گوشی هم روی دسکتاپ) ----------
MAX_CHARS_PER_LINE = 26      # حدوداً ۴-۵ کلمه‌ی فارسی در هر خط
CHAR_WIDTH = dp(9.5)        # تخمین عرض هر حرف - عمداً یکم بیشتر از حد نیاز واقعی
                             # تا هیچ‌وقت کمتر از عرض واقعی متن نشه (وگرنه Kivy
                             # خودش تصمیم می‌گیره متن رو بشکنه و می‌ره روی ساعت)
MIN_BUBBLE_WIDTH = dp(100)  # باید حتماً جا برای متن ساعت + تیک (✓✓) هم داشته باشه
LINE_HEIGHT = dp(24)
TIME_ROW_HEIGHT = dp(16)
LINE_SPACING = dp(2)
BUBBLE_PAD_TOP = dp(10)
BUBBLE_PAD_BOTTOM = dp(6)
BUBBLE_PAD_SIDE = dp(14)
BUBBLE_FONT_SIZE = "15sp"
TIME_FONT_SIZE = "11sp"


class FarsiTextField(MDTextField):
    """
    MDTextField معمولی هر حرف فارسی رو جدا نمایش می‌ده (بهم نمی‌چسبن)
    چون Kivy حین تایپ، حروف رو reshape نمی‌کنه.
    این کلاس فقط نحوه‌ی *نمایش* متن داخل جعبه رو مجبور می‌کنه از fa() رد بشه،
    بدون اینکه متن واقعی ذخیره‌شده (self.text) رو تغییر بده.
    """
    def _create_line_label(self, text, hint=False):
        return super()._create_line_label(fa(text), hint=hint)


def _wrap_by_words(text, max_chars=MAX_CHARS_PER_LINE):
    """
    متن رو کلمه‌به‌کلمه به چند خط می‌شکنه، فقط با شمردن تعداد حرف (نه
    اندازه‌گیری واقعی روی صفحه)، پس همیشه قطعی و بدون وابستگی به
    تایمینگ یا رندر فونته.
    """
    words = text.split(" ")
    lines = []
    current = []
    current_len = 0
    for word in words:
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > max_chars:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra
    if current:
        lines.append(" ".join(current))
    return lines or [text]


def _fixed_label(text, width, height, **kwargs):
    """
    یه MDLabel با عرض و ارتفاع *دقیقاً مشخص‌شده* (نه خودکار)، راست‌چین.
    این‌جوری همه‌چیز از همون لحظه‌ی اول قطعیه، هیچ وابستگی به
    texture_size یا adaptive_size که قبلاً مشکل‌ساز بودن نداریم.
    """
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


class ChatScreen(MDScreen):
    name ="chat"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.previous_screen = "main"
        self.typing_label = None
        self.message_log = []  # [(text, is_user), ...] - برای بازسازی حباب‌ها وقتی تنظیمات عوض می‌شه
        app = MDApp.get_running_app()
        if app:
            app.theme_cls.bind(theme_style=self._on_theme_change)
            app.bind(chat_setting=self._on_settings_change)
        self.build_chat()

    # ==================================================
    # ساخت رابط کاربری
    # ==================================================
    def build_chat(self):
        try:
            print("✅ build_chat started")
            c = get_colors()
            self.main_layout = MDBoxLayout(orientation="vertical", md_bg_color=c["BACKGROUND"])

            self.toolbar = MDTopAppBar()
            set_toolbar_title(self.toolbar, "پشتیبانی")
            self.toolbar.pos_hint = {"top": 1}
            self.toolbar.left_action_items = [["arrow-left", lambda x: self.go_back()]]
            self.toolbar.md_bg_color = ACCENT
            self.toolbar.specific_text_color = TEXT_ON_ACCENT
            self.toolbar.elevation = 2
            self.main_layout.add_widget(self.toolbar)

            self.scroll_view = ScrollView(bar_width=0, do_scroll_x=False)
            self.chat_layout = MDBoxLayout(
                orientation="vertical",
                size_hint_y=None,
                spacing="8dp",
                padding=["10dp", "14dp", "10dp", "14dp"],
                md_bg_color=c["BACKGROUND"],
            )
            self.chat_layout.bind(minimum_height=self.chat_layout.setter("height"))
            self.scroll_view.add_widget(self.chat_layout)
            self.main_layout.add_widget(self.scroll_view)

            self.bottom_layout = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="60dp",
                spacing="8dp",
                padding=["10dp", "8dp", "10dp", "8dp"],
                md_bg_color=c["SURFACE"],
            )

            self.text_input = FarsiTextField(
                hint_text="Type a message...",
                font_name=FONT_NAME,
                mode="round",
                multiline=False,
                foreground_color=c["TEXT_DARK"],
                size_hint_x=1,
                line_color_normal=(0.85, 0.85, 0.88, 1),
                line_color_focus=ACCENT,
            )
            lock_font_forever(self.text_input)
            self.text_input.bind(text=self.on_text_change)
            self.text_input.bind(on_text_validate=self.send_message)

            self.send_button = MDIconButton(
                icon="send",
                size_hint_x=None,
                width="44dp",
                md_bg_color=(0.9, 0.9, 0.92, 1),
                theme_text_color="Custom",
                text_color=c["TEXT_MUTED"],
                on_press=self.send_message,
            )

            self.bottom_layout.add_widget(self.text_input)
            self.bottom_layout.add_widget(self.send_button)
            self.main_layout.add_widget(self.bottom_layout)

            #try:
            #    self.main_layout.add_widget(Factory.BottomBar())
            #except Exception as e:
            #    print(f"⚠️ BottomBar not added: {e}")

            self.add_sample_message()
            Clock.schedule_once(lambda dt: self.add_widget(self.main_layout))
            print("✅ build_chat finished")
        except Exception as e:
            print(f"❌ ERROR in build_chat: {e}")
            import traceback
            traceback.print_exc()

    def go_back(self):
        app = MDApp.get_running_app()
        if app:
            app.go_back()
        else:
            self.manager.current = self.previous_screen

    # ==================================================
    # دارک‌مود
    # ==================================================
    def _on_theme_change(self, *args):
        c = get_colors()
        self.main_layout.md_bg_color = c["BACKGROUND"]
        self.chat_layout.md_bg_color = c["BACKGROUND"]
        self.bottom_layout.md_bg_color = c["SURFACE"]
        self.text_input.foreground_color = c["TEXT_DARK"]
        self.send_button.text_color = c["TEXT_MUTED"]

    # ==================================================
    # نشانگر "در حال تایپ"
    # ==================================================
    def _on_settings_change(self, *args):
        """
        وقتی تو تنظیمات چیزی عوض می‌شه (مثلاً رسید خوانده‌شدن خاموش
        می‌شه)، کل حباب‌های چت رو با تنظیمات جدید دوباره می‌سازیم تا
        پیام‌های قدیمی هم فوراً به‌روز بشن (نه فقط پیام‌های بعدی).
        """
        if not self._typing_indicator_enabled() and self.typing_label and self.typing_label.parent:
            self.chat_layout.remove_widget(self.typing_label)
            self.typing_label = None

        self.chat_layout.clear_widgets()
        for text, is_user in self.message_log:
            bubble = self.create_message_bubble(text, is_user)
            self.chat_layout.add_widget(bubble)

    def _typing_indicator_enabled(self):
        app = MDApp.get_running_app()
        settings = getattr(app, "chat_setting", None)
        if settings is None:
            return True
        return settings.get("typing_indicator", True)

    def on_text_change(self, instance, value):
        if value.strip() and not self.typing_label and self._typing_indicator_enabled():
            self.typing_label = self._build_typing_bubble()
            self.chat_layout.add_widget(self.typing_label)
            Clock.schedule_once(self.clear_typing_indicator, 2)

        elif not value.strip() and self.typing_label and self.typing_label.parent:
            self.chat_layout.remove_widget(self.typing_label)
            self.typing_label = None

        c = get_colors()
        if value.strip():
            self.send_button.md_bg_color = ACCENT_GREEN
            self.send_button.text_color = TEXT_ON_ACCENT
        else:
            self.send_button.md_bg_color = (0.9, 0.9, 0.92, 1)
            self.send_button.text_color = c["TEXT_MUTED"]

    def _build_typing_bubble(self):
        c = get_colors()
        row = MDBoxLayout(size_hint_y=None, height=dp(36), padding=[4, 2, 4, 2])
        text = fa("...در حال تایپ")
        width = max(dp(90), len(text) * CHAR_WIDTH)
        card = MDCard(
            orientation="vertical",
            size_hint=(None, None),
            size=(width + dp(24), dp(30)),
            radius=[14, 14, 14, 4],
            md_bg_color=c["BUBBLE_SUPPORT"],
            padding=["12dp", "5dp"],
            elevation=1,
        )
        label = _fixed_label(
            text,
            width=width,
            height=dp(20),
            font_name=FONT_NAME,
            theme_text_color="Custom",
            text_color=c["TEXT_MUTED"],
            font_size=TIME_FONT_SIZE,
            halign="right",
        )
        card.add_widget(label)
        row.add_widget(card)
        row.add_widget(Widget())
        return row

    def clear_typing_indicator(self, dt):
        if self.typing_label and self.typing_label.parent:
            self.chat_layout.remove_widget(self.typing_label)
            self.typing_label = None

    # ==================================================
    # حباب‌های پیام
    # ==================================================
    def add_sample_message(self):
        sample_messages = [
            ("سلام! به پشتیبانی خوش اومدی. چطور می‌تونم کمکت کنم؟", False),
            ("سلام، یه سوال درباره‌ی دوره‌ی پایتون داشتم", True),
            ("حتماً! چی می‌خوای بدونی؟", False),
            ("آخرش مدرک هم می‌ده؟", True),
            ("بله، مدرک رسمی دریافت می‌کنی", False),
        ]
        for msg, is_user in sample_messages:
            self.message_log.append((msg, is_user))
            bubble = self.create_message_bubble(msg, is_user)
            self.chat_layout.add_widget(bubble)

    def create_message_bubble(self, text, is_user=True, simulate_read=False):
        """
        حباب پیام به سبک تلگرام. همه‌ی اندازه‌ها (عرض، ارتفاع هر خط،
        ارتفاع کل حباب) از قبل و مستقیم محاسبه می‌شن - هیچ‌چیز به
        adaptive_size یا texture_size (که قبلاً مشکل‌ساز بودن) واگذار
        نمی‌شه.

        simulate_read=True یعنی این پیام تازه فرستاده شده: اول با یه
        تیک (ارسال‌شد) نشون داده می‌شه، بعد از یه تاخیر کوتاه خودکار
        دو-تیک (دیده‌شد) می‌شه - یه شبیه‌سازیه، به یه رخداد واقعی
        "دیدن پیام توسط طرف مقابل" وصل نیست چون بک‌اند واقعی نداریم.
        """
        c = get_colors()
        if is_user:
            bubble_color = BUBBLE_USER
            text_color = TEXT_ON_ACCENT
            time_color = (1, 1, 1, 0.75)
            radius = [16, 16, 4, 16]
            side = "right"
        else:
            bubble_color = c["BUBBLE_SUPPORT"]
            text_color = c["TEXT_DARK"]
            time_color = c["TEXT_MUTED"]
            radius = [16, 16, 16, 4]
            side = "left"

        # طبق درخواست، پیام هیچ‌وقت نمی‌شکنه؛ همیشه یه خطه. این باعث
        # می‌شه ارتفاع حباب همیشه یه عدد ثابت و قطعی باشه و دیگه هیچ‌وقت
        # با ردیف ساعت قاطی نشه.
        lines = [text]

        now = datetime.now()
        time_str = now.strftime("%H:%M")
        # نکته: علامت تیک رو دیگه به‌صورت کاراکتر متنی (✓✓) داخل رشته
        # نمی‌ذاریم، چون فونت فارسی (Vazirmatn) این علامت رو نداره و
        # اصلاً رندر نمی‌شد. به‌جاش یه آیکون واقعی جدا کنارش می‌ذاریم.
        time_text = time_str

        # عرض حباب باید هم برای متن پیام کافی باشه، هم برای ساعت (وگرنه
        # تو پیام‌های خیلی کوتاه، ساعت می‌شکست و روی متن می‌افتاد)
        extra_for_checkmark = dp(20) if is_user else 0
        content_width = max(
            MIN_BUBBLE_WIDTH,
            len(fa(text)) * CHAR_WIDTH,
            len(time_text) * CHAR_WIDTH + extra_for_checkmark,
        ) + dp(8)  # یه حاشیه‌ی امن اضافه، تا حتی اگه تخمین یکم کم بود، مشکلی پیش نیاد

        # ارتفاع کل حباب: مستقیم و دقیق حساب می‌شه، نه با adaptive_size
        bubble_width = content_width + (BUBBLE_PAD_SIDE * 2)
        bubble_height = (
            BUBBLE_PAD_TOP
            + BUBBLE_PAD_BOTTOM
            + (len(lines) * LINE_HEIGHT)
            + (max(len(lines) - 1, 0) * LINE_SPACING)
            + LINE_SPACING
            + TIME_ROW_HEIGHT
        )

        bubble = MDCard(
            orientation="vertical",
            size_hint=(None, None),
            size=(bubble_width, bubble_height),
            radius=radius,
            md_bg_color=bubble_color,
            padding=[BUBBLE_PAD_SIDE, BUBBLE_PAD_TOP, BUBBLE_PAD_SIDE, BUBBLE_PAD_BOTTOM],
            spacing=LINE_SPACING,
            elevation=1,
        )

        for line in lines:
            line_label = _fixed_label(
                fa(line),
                width=content_width,
                height=LINE_HEIGHT,
                font_name=FONT_NAME,
                font_size=BUBBLE_FONT_SIZE,
                theme_text_color="Custom",
                text_color=text_color,
                halign="right",
            )
            bubble.add_widget(line_label)

        # ---------- ساعت + تیک (آیکون واقعی)، داخل خود حباب ----------
        time_row = MDBoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            width=content_width,
            height=TIME_ROW_HEIGHT,
            spacing=dp(2),
        )
        time_row.add_widget(Widget())  # فاصله‌ی خالی که همه‌چیز رو به راست هول می‌ده
        app = MDApp.get_running_app()
        read_receipts_on = True
        if app is not None:
            read_receipts_on = getattr(app, "chat_setting", {}).get("read_receipts", True)
        check_icon = None
        if is_user and read_receipts_on:
            check_icon = MDIcon(
                icon="check" if simulate_read else "check-all",
                theme_text_color="Custom",
                text_color=time_color,
                font_size="14sp",
                size_hint=(None, None),
                size=(dp(18), TIME_ROW_HEIGHT),
                halign="center",
                valign="middle",
            )
            time_row.add_widget(check_icon)
            if simulate_read:
                # بعد از یه تاخیر کوتاه، تیک تنها رو دو-تیک می‌کنیم
                # (شبیه‌سازی "دیده شدن" - واقعی نیست، چون بک‌اند نداریم)
                Clock.schedule_once(lambda dt: setattr(check_icon, "icon", "check-all"), 1.5)
        time_label = _fixed_label(
            time_text,
            width=len(time_text) * CHAR_WIDTH + dp(6),
            height=TIME_ROW_HEIGHT,
            font_name=FONT_NAME,
            font_size=TIME_FONT_SIZE,
            theme_text_color="Custom",
            text_color=time_color,
            halign="right",
        )
        time_row.add_widget(time_label)
        bubble.add_widget(time_row)

        # ---------- ردیف: حباب + فاصله‌ی خالی برای هول دادن به سمت درست ----------
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=bubble_height + dp(4),
            padding=[6, 2, 6, 2],
        )
        if side == "right":
            row.add_widget(Widget())
            row.add_widget(bubble)
        else:
            row.add_widget(bubble)
            row.add_widget(Widget())

        return row

    # ==================================================
    # ارسال پیام
    # ==================================================
    def send_message(self, instance):
        message_text = self.text_input.text
        if not message_text.strip():
            return

        if self.typing_label and self.typing_label.parent:
            self.chat_layout.remove_widget(self.typing_label)
            self.typing_label = None

        user_bubble = self.create_message_bubble(message_text, is_user=True, simulate_read=True)
        self.message_log.append((message_text, True))
        self.chat_layout.add_widget(user_bubble)
        self.text_input.text = ""
        Animation(scroll_y=0, d=0.3, t="in_out_cubic").start(self.scroll_view)

        reply_text = "پیامت دریافت شد! به‌زودی جواب می‌دیم"
        support_bubble = self.create_message_bubble(reply_text, False)
        self.message_log.append((reply_text, False))
        self.chat_layout.add_widget(support_bubble)
        Animation(scroll_y=0, d=0.3, t="in_out_cubic").start(self.scroll_view)
        Clock.schedule_once(lambda dt: setattr(self.text_input, "focus", True), 0.1)