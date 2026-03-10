# ============================================================
# contact/models.py
# Contact yuborish uchun model
# Faqat ro'yxatdan o'tgan foydalanuvchilar yuborishi mumkin!
# ============================================================

from django.db import models
from shared.models import BaseModel
from user.models import User


class Contact(BaseModel):
    """
    Foydalanuvchilar yuboradigan kontakt (murojaat) modeli.

    Qoidalar:
    - Faqat ro'yxatdan O'TGAN foydalanuvchilar yuborishi mumkin
    - Ya'ni auth_status='done' yoki 'photo_done' bo'lishi kerak
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    # Kimdan → foydalanuvchi

    subject = models.CharField(max_length=255)
    # Mavzu

    message = models.TextField()
    # Xabar matni

    is_read = models.BooleanField(default=False)

    # Admin tomonidan o'qilganmi

    def __str__(self):
        return f'{self.user.phone_number} - {self.subject}'