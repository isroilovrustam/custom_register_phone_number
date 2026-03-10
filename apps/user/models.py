import uuid
from datetime import timedelta
import random
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from shared.models import BaseModel
from django.db import models

NEW, CODE, DONE, PHOTO_DONE = ('new', 'code', 'done', 'photo_done')

ORDINARY, MANAGER, ADMIN = ('ordinary', 'manager', 'admin')


class User(AbstractUser, BaseModel):
    AUTH_STATUS_CHOICES = (
        (NEW, NEW),
        (CODE, CODE),
        (DONE, DONE),
        (PHOTO_DONE, PHOTO_DONE),
    )
    USER_ROLES = (
        (ORDINARY, ORDINARY),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN),
    )

    auth_status = models.CharField(max_length=10, choices=AUTH_STATUS_CHOICES, default=NEW)
    # Ro'yxatdan o'tish bosqichi → default: 'new'

    user_role = models.CharField(max_length=10, choices=USER_ROLES, default=ORDINARY)
    # Foydalanuvchi roli → default: 'ordinary'

    phone_number = models.CharField(max_length=11, unique=True)
    # Telefon raqam — takrorlanmas bo'lishi shart!

    photo = models.ImageField(upload_to='user/photos', null=True, blank=True)

    # Rasm — ixtiyoriy, user/photos/ papkasiga saqlanadi

    def __str__(self):
        return f'{self.phone_number}-{self.username or "Mavjud emas"}'

    @property
    def full_name(self):
        """Ism va familiyani birlashtiradi: 'Ali Valiyev'"""
        return f'{self.first_name} {self.last_name}'

    def create_verify_code(self):
        """
        4 xonali tasdiqlash kodi yaratadi va Confirmation jadvaliga saqlaydi.
        Misol: '4823'
        """
        code = "".join([str(random.randint(0, 10000) % 10) for _ in range(4)])
        Confirmation.objects.create(
            user_id=self.id,
            code=code,
        )
        return code  # Kod qaytariladi → emailga yuborish uchun

    def check_username(self):
        """
        Agar username yo'q bo'lsa, avtomatik yaratadi.
        Format: 'instagram-a2f3b1c4'
        Takrorlanmasligini ham tekshiradi.
        """
        if not self.username:
            temp_username = f'instagram-{uuid.uuid4().__str__().split("-")[-1]}'
            while User.objects.filter(username=temp_username):
                temp_username = f"{temp_username}{random.randint(0, 9)}"
            self.username = temp_username

    def check_pass(self):
        """
        Agar parol yo'q bo'lsa, vaqtinchalik parol yaratadi.
        Format: 'password-a2f3b1c4'
        Keyinchalik foydalanuvchi o'zi o'zgartiradi.
        """
        if not self.password:
            temp_password = f'password-{uuid.uuid4().__str__().split("-")[-1]}'
            self.password = temp_password

    def hashing_password(self):
        """
        Parolni xeshlaydi (shifrlaydi).
        Agar parol allaqachon xeshlangan bo'lsa ('pbkdf2_sha256' bilan boshlanadi) → o'tkazib yuboradi.
        """
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)

    def token(self):
        """
        JWT tokenlarni yaratadi va qaytaradi.
        access: Qisqa muddatli token (2 kun)
        refresh_token: Yangilash uchun token (15 kun)
        """
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh_token": str(refresh)
        }

    def save(self, *args, **kwargs):
        """Saqlashdan oldin clean() chaqiriladi"""
        self.clean()
        super(User, self).save(*args, **kwargs)

    def clean(self):
        """
        Saqlashdan oldin avtomatik:
        1. Username tekshiriladi/yaratiladi
        2. Parol tekshiriladi/yaratiladi
        3. Parol xeshlanadi
        """
        self.check_username()
        self.check_pass()
        self.hashing_password()


class Confirmation(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confirmations')
    code = models.CharField(max_length=4)
    expiration_time = models.DateTimeField()

    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.phone_number}-{self.code}'

    def save(self, *args, **kwargs):
        self.expiration_time = timezone.now() + timedelta(minutes=2)
        super(Confirmation, self).save(*args, **kwargs)
