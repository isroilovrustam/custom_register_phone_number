from django.contrib import admin
from django.utils.html import format_html
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Foydalanuvchilar yuborgan murojaatlar ro'yxati.
    Faqat ro'yxatdan TO'LIQ o'tgan foydalanuvchilar yuborishi mumkin.
    """

    # --- Ro'yxat sahifasi ---
    list_display = (
        'id',
        'user_phone',       # Yuboruvchi telefon (custom)
        'user_fullname',    # Yuboruvchi ism-familiya (custom)
        'subject',          # Mavzu
        'short_message',    # Qisqa xabar (custom)
        'is_read_badge',    # O'qilganlik belgisi (custom)
        'created_at',       # Yuborilgan vaqt
    )

    list_display_links = ('id', 'subject')

    list_filter = (
        'is_read',      # O'qilgan / O'qilmagan
        'created_at',   # Sana bo'yicha
    )

    search_fields = (
        'user__phone_number',  # Telefon bo'yicha qidirish
        'user__first_name',    # Ism bo'yicha
        'subject',             # Mavzu bo'yicha
        'message',             # Xabar matni bo'yicha
    )

    ordering = ('-created_at',)
    # Yangi murojaatlar birinchi

    readonly_fields = (
        'user',
        'subject',
        'message',
        'created_at',
        'updated_at',
    )
    # Admindan murojaatni o'zgartirish taqiqlangan
    # Faqat is_read ni o'zgartirish mumkin

    list_per_page = 20

    # --- Batafsil sahifa bo'limlari ---
    fieldsets = (
        ("📨 Murojaat ma'lumotlari", {
            'fields': (
                'user',
                'subject',
                'message',
                'is_read',
            )
        }),
        ('⏰ Vaqt', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # --- Custom ustun metodlari ---

    def user_phone(self, obj):
        """Yuboruvchining telefon raqami."""
        return obj.user.phone_number

    user_phone.short_description = '📱 Telefon'

    def user_fullname(self, obj):
        """Yuboruvchining ism-familiyasi."""
        name = f'{obj.user.first_name} {obj.user.last_name}'.strip()
        return name if name else '—'

    user_fullname.short_description = '👤 Ism Familiya'

    def short_message(self, obj):
        """
        Xabarning birinchi 60 belgisini ko'rsatadi.
        Uzunroq bo'lsa '...' qo'shiladi.
        """
        if len(obj.message) > 60:
            return obj.message[:60] + '...'
        return obj.message

    short_message.short_description = '💬 Xabar'

    def is_read_badge(self, obj):
        """
        O'qilganlik holatini rangli badge bilan ko'rsatadi.
        O'qilgan   → 🟢 Yashil
        O'qilmagan → 🔴 Qizil (diqqatni tortadi)
        """
        if obj.is_read:
            return format_html(
                '<span style="'
                'background-color: #00aa44; '
                'color: white; '
                'padding: 3px 10px; '
                'border-radius: 12px; '
                'font-size: 12px;'
                '">✅ O\'qilgan</span>'
            )
        return format_html(
            '<span style="'
            'background-color: #ff4444; '
            'color: white; '
            'padding: 3px 10px; '
            'border-radius: 12px; '
            'font-size: 12px; '
            'font-weight: bold;'
            '">🔴 Yangi</span>'
        )

    is_read_badge.short_description = 'Holat'

    # --- Ommaviy amallar ---
    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='✅ O\'qilgan deb belgilash')
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} ta murojaat o\'qilgan deb belgilandi.')

    @admin.action(description='🔴 O\'qilmagan deb belgilash')
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} ta murojaat o\'qilmagan deb belgilandi.')

    # Batafsil sahifani ochganda avtomatik o'qilgan deb belgilash
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Admin murojaat sahifasini ochganda avtomatik
        is_read = True ga o'zgaradi.
        """
        response = super().change_view(request, object_id, form_url, extra_context)
        try:
            obj = Contact.objects.get(pk=object_id)
            if not obj.is_read:
                obj.is_read = True
                obj.save()
        except Contact.DoesNotExist:
            pass
        return response