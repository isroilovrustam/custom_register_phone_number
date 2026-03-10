# ============================================================
# apps/user/admin.py — Foydalanuvchi admin paneli
# ============================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Confirmation


# ============================================================
# Confirmation ni User ichida ko'rsatish uchun Inline
# ============================================================
class ConfirmationInline(admin.TabularInline):
    """
    User sahifasini ochganda, pastda shu foydalanuvchining
    tasdiqlash kodlari ham ko'rinadi.

    TabularInline → jadval ko'rinishida
    StackedInline → vertikal ko'rinishda (muqobil)
    """
    model = Confirmation
    extra = 0
    # extra=0 → bo'sh qo'shimcha qatorlar ko'rsatilmaydi

    readonly_fields = ('code', 'expiration_time', 'is_confirmed', 'created_at')
    # Bu maydonlar o'qish uchun — admindan o'zgartirish mumkin emas

    can_delete = False
    # Admindan o'chirish taqiqlangan

    fields = ('code', 'expiration_time', 'is_confirmed', 'created_at')
    # Inline da qaysi maydonlar ko'rinsin


# ============================================================
# User Admin
# ============================================================
@admin.register(User)
class UserAdmin(UserAdmin):
    """
    Foydalanuvchilar ro'yxati va batafsil sahifasi.

    @admin.register(User) → admin.site.register(User, UserAdmin) bilan bir xil,
    lekin qisqaroq va zamonaviy usul.
    """

    # --- Ro'yxat sahifasi ko'rinishi ---
    list_display = (
        'id',
        'phone_number',        # Telefon raqam
        'full_name',           # Ism Familiya
        'auth_status_badge',   # Rangli holat belgisi (custom metod)
        'user_role',           # Roli
        'photo_preview',       # Kichik rasm ko'rinishi
        'is_active',           # Faolmi
        'created_at',          # Ro'yxatdan o'tgan sana
    )

    list_display_links = ('id', 'phone_number')
    # Bosib kirish mumkin bo'lgan ustunlar

    list_filter = (
        'auth_status',   # Holat bo'yicha filterlash
        'user_role',     # Rol bo'yicha filterlash
        'is_active',     # Faollik bo'yicha
        'created_at',    # Sana bo'yicha
    )

    search_fields = (
        'phone_number',   # Telefon raqam bo'yicha qidirish
        'first_name',     # Ism bo'yicha
        'last_name',      # Familiya bo'yicha
        'username',       # Username bo'yicha
    )

    ordering = ('-created_at',)
    # Yangi foydalanuvchilar birinchi ko'rinadi

    readonly_fields = (
        'id',
        'last_login',
        'created_at',
        'updated_at',
        'photo_preview_large',  # Katta rasm ko'rinishi
    )

    inlines = [ConfirmationInline]
    # User sahifasini ochganda tasdiqlash kodlari ham ko'rinadi

    # --- Batafsil sahifa bo'limlari ---
    fieldsets = (
        # Bo'lim 1: Asosiy ma'lumotlar
        ("👤 Asosiy ma'lumotlar", {
            'fields': (
                'id',
                'phone_number',
                'username',
                'first_name',
                'last_name',
                'photo',
                'photo_preview_large',
            )
        }),

        # Bo'lim 2: Holat va rol
        ('📊 Holat va Rol', {
            'fields': (
                'auth_status',
                'user_role',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),

        # Bo'lim 3: Parol (UserAdmin dan meros)
        ('🔒 Parol', {
            'fields': ('password',),
            'classes': ('collapse',),
            # collapse → bu bo'lim yig'ilgan (ochish mumkin)
        }),

        # Bo'lim 4: Vaqt ma'lumotlari
        ("⏰ Vaqt ma'lumotlari", {
            'fields': (
                'last_login',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    # Yangi foydalanuvchi qo'shish sahifasi uchun alohida fieldsets
    add_fieldsets = (
        ('➕ Yangi foydalanuvchi', {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'auth_status',
                'user_role',
                'is_active',
            ),
        }),
    )

    # --- Ko'rsatkichlar (har sahifada nechta) ---
    list_per_page = 25
    # Bir sahifada 25 ta foydalanuvchi

    list_max_show_all = 100
    # "Barchasini ko'rsatish" bosilganda maksimum 100 ta

    # --- Custom ustun metodlari ---

    def auth_status_badge(self, obj):
        """
        auth_status ni rangli badge ko'rinishida chiqaradi.

        new       → 🔴 Qizil  (boshlang'ich)
        code      → 🟡 Sariq  (kod kutilmoqda)
        done      → 🟢 Yashil (tayyor)
        photo_done → 🔵 Ko'k  (to'liq)
        """
        colors = {
            'new': ('#ff4444', '🔴 Yangi'),
            'code': ('#ffaa00', '🟡 Kod kutilmoqda'),
            'done': ('#00aa44', '🟢 Tayyor'),
            'photo_done': ('#0088ff', '🔵 To\'liq'),
        }
        color, label = colors.get(obj.auth_status, ('#999', obj.auth_status))
        return format_html(
            '<span style="'
            'background-color: {}; '
            'color: white; '
            'padding: 3px 10px; '
            'border-radius: 12px; '
            'font-size: 12px; '
            'font-weight: bold;'
            '">{}</span>',
            color, label
        )

    auth_status_badge.short_description = 'Holat'
    # Ustun sarlavhasi

    def photo_preview(self, obj):
        """
        Ro'yxatda kichik doiraviy rasm ko'rsatadi.
        """
        if obj.photo:
            return format_html(
                '<img src="{}" style="'
                'width: 35px; '
                'height: 35px; '
                'border-radius: 50%; '
                'object-fit: cover; '
                'border: 2px solid #ddd;'
                '" />',
                obj.photo.url
            )
        return format_html(
            '<span style="'
            'color: #999; '
            'font-size: 11px;'
            '">Rasm yo\'q</span>'
        )

    photo_preview.short_description = 'Rasm'

    def photo_preview_large(self, obj):
        """
        Batafsil sahifada katta rasm ko'rsatadi.
        """
        if obj.photo:
            return format_html(
                '<img src="{}" style="'
                'width: 120px; '
                'height: 120px; '
                'border-radius: 10px; '
                'object-fit: cover; '
                'border: 3px solid #ddd;'
                '" />',
                obj.photo.url
            )
        return 'Rasm yuklanmagan'

    photo_preview_large.short_description = 'Rasm ko\'rinishi'

    def full_name(self, obj):
        """
        Ism va familiyani birlashtiradi.
        Agar ikkalasi ham yo'q bo'lsa — chiziqcha ko'rsatadi.
        """
        name = f'{obj.first_name} {obj.last_name}'.strip()
        return name if name else '—'

    full_name.short_description = 'Ism Familiya'

    # --- Ommaviy amallar (Actions) ---
    actions = ['make_active', 'make_inactive', 'reset_auth_status']

    @admin.action(description='✅ Tanlangan foydalanuvchilarni faollashtirish')
    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} ta foydalanuvchi faollashtirildi.')

    @admin.action(description='🚫 Tanlangan foydalanuvchilarni bloklash')
    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} ta foydalanuvchi blok qilindi.')

    @admin.action(description='🔄 auth_status ni "new" ga qaytarish')
    def reset_auth_status(self, request, queryset):
        count = queryset.update(auth_status='new')
        self.message_user(request, f'{count} ta foydalanuvchining holati yangilandi.')


# ============================================================
# Confirmation Admin
# ============================================================
@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    """
    Tasdiqlash kodlari ro'yxati va batafsil sahifasi.
    """

    list_display = (
        'id',
        'user_phone',       # Foydalanuvchi telefoni (custom)
        'code',             # 4 xonali kod
        'is_confirmed',     # Tasdiqlanganligi
        'expiration_time',  # Muddati
        'is_expired',       # Muddati o'tganmi (custom)
        'created_at',       # Yaratilgan vaqt
    )

    list_display_links = ('id', 'user_phone')

    list_filter = (
        'is_confirmed',
        'created_at',
    )

    search_fields = (
        'user__phone_number',   # Ikki pastki chiziq → related field
        'code',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'user',
        'code',
        'expiration_time',
        'created_at',
        'updated_at',
    )

    list_per_page = 30

    # --- Custom ustun metodlari ---

    def user_phone(self, obj):
        """Foydalanuvchi telefon raqamini chiqaradi."""
        return obj.user.phone_number

    user_phone.short_description = 'Telefon raqam'

    def is_expired(self, obj):
        """
        Tasdiqlash kodining muddati o'tganmi yoki yo'qligini tekshiradi.
        """
        from django.utils import timezone
        if obj.expiration_time and obj.expiration_time < timezone.now():
            return format_html(
                '<span style="color: red; font-weight: bold;">⌛ Muddati o\'tgan</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">✅ Amal qilmoqda</span>'
        )

    is_expired.short_description = 'Holati'

    # Tasdiqlangan kodlarni ommaviy o'chirish
    actions = ['delete_confirmed_codes']

    @admin.action(description='🗑️ Tasdiqlangan kodlarni o\'chirish')
    def delete_confirmed_codes(self, request, queryset):
        count = queryset.filter(is_confirmed=True).delete()[0]
        self.message_user(request, f'{count} ta tasdiqlangan kod o\'chirildi.')