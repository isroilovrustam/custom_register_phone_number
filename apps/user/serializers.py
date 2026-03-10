from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from django.db.models import Q

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utilis import check_phone_number, send_email, send_phone_code, check_user_type
from .models import User, Confirmation, NEW, CODE, DONE, PHOTO_DONE

class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = User
        fields = ("id", "auth_status", "phone_number")
        extra_kwargs = {
            "auth_status": {"read_only": True, "required": False}
        }

    def validate(self, data):
        """
        Umumiy validatsiya metodi.
        Avval standart Django tekshiruvi, keyin telefon tekshiruvi.
        """
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        """
        Telefon raqam formatini tekshiradi.

        Agar to'g'ri telefon raqam → {'phone_number': '+998901234567'} qaytaradi
        Agar noto'g'ri format    → ValidationError chiqaradi

        @staticmethod — bu metod self ga muhtoj emas, shuning uchun static
        """
        user_input = str(data.get("phone_number")).lower()
        input_type = check_phone_number(user_input)

        if input_type == "phone":
            data = {
                "phone_number": user_input,
            }
        else:
            data = {
                "success": False,
                "message": "Telefon raqam yoki email jonatishing shart"
            }
            raise ValidationError(data)

        return data

    def validate_phone_number(self, value):
        value = value.lower()
        if value and User.objects.filter(phone_number=value).exists():
            data = {
                "success": False,
                "message": "Bu telefon raqami allaqachon ma'lumotlar bazasida bor"
            }
            raise ValidationError(data)

        return value

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        code = user.create_verify_code()
        send_email(user.phone_number, code)
        user.save()
        return user

    def to_representation(self, instance):
        """
        Javob formatini o'zgartiradi.

        Standart javob: {"id": "...", "auth_status": "new"}
        Bizning javob:  {"id": "...", "auth_status": "new",
                         "access": "jwt...", "refresh_token": "jwt..."}

        to_representation() → ma'lumot foydalanuvchiga qaytarilishidan oldin chaqiriladi
        """
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())

        return data


# ============================================================
# 2. ChangeUserInformation — Ma'lumotlarni to'ldirish serialayzeri
# ============================================================
# Vazifasi:
#   - Foydalanuvchi kod tasdiqlangandan keyin ma'lumotlarini to'ldiradi
#   - ism, familiya, username, parol qabul qilinadi
#   - Parollar mos kelishini tekshiradi
#   - Username uzunligini va formatini tekshiradi
#   - auth_status ni 'code' → 'done' ga o'zgartiradi
# ============================================================

class ChangeUserInformation(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """
        Umumiy validatsiya:
        1. Ikki parol bir-biriga tengmi?
        2. Parol kuchli (Django standartiga mos)mi?
        """
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password != confirm_password:
            raise ValidationError(
                {
                    "message": "Parolingiz va tasdiqlash parolingiz bir-biriga teng emas"
                }
            )

        if password:
            # Django'ning standart parol tekshiruvi:
            # - Minimum 8 belgi
            # - Faqat raqamdan iborat bo'lmasin
            # - Juda keng tarqalgan bo'lmasin (12345678 kabi)
            # - Foydalanuvchi ma'lumotlariga o'xshab ketmasin
            validate_password(password)
            validate_password(confirm_password)

        return data

    def validate_username(self, username):
        """
        Username uchun qo'shimcha tekshiruvlar:
        - 5 dan 30 belgigacha bo'lishi kerak
        - Faqat raqamdan iborat bo'lmasin

        Django avtomatik chaqiradi: validate_<maydon_nomi>()
        """
        if len(username) < 5 or len(username) > 30:
            raise ValidationError(
                {
                    "message": "Username must be between 5 and 30 characters long"
                }
            )

        if username.isdigit():
            # isdigit() → '12345' kabi faqat raqamlar → True qaytaradi
            raise ValidationError(
                {
                    "message": "This username is entirely numeric"
                }
            )

        return username

    def update(self, instance, validated_data):
        """
        Foydalanuvchi ma'lumotlarini yangilaydi.

        instance → joriy User obyekti
        validated_data → tekshirilgan ma'lumotlar

        .get('kalit', standart_qiymat) → agar kalit yo'q bo'lsa, eski qiymat qoladi
        """
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)

        if validated_data.get('password'):
            # set_password() → parolni xeshlaydi (shifrlaydi)
            # Agar oddiy saqlasak, parol ochiq ko'rinadi → xavfli!
            instance.set_password(validated_data.get('password'))

        if instance.auth_status == CODE:
            # Kod tasdiqlangan va ma'lumotlar to'ldirildi
            # 'code' → 'done' ga o'tkaziladi
            instance.auth_status = DONE

        instance.save()
        return instance


# ============================================================
# 3. ChangeUserPhotoSerializer — Rasm yuklash serialayzeri
# ============================================================
# Vazifasi:
#   - Foydalanuvchi profiliga rasm yuklaydi
#   - Rasm formatini tekshiradi (faqat ruxsat etilganlar)
#   - auth_status ni 'done' → 'photo_done' ga o'zgartiradi
#   - Ro'yxatdan o'tish bu bilan TO'LIQ yakunlanadi
# ============================================================

class ChangeUserPhotoSerializer(serializers.Serializer):

    photo = serializers.ImageField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'jpg',   # Standart rasm formati
                    'jpeg',  # Standart rasm formati
                    'png',   # Shaffof fon qo'llab-quvvatlanadi
                    'heic',  # iPhone yangi formati
                    'heif'   # iPhone yangi formati
                ]
            )
        ]
    )
    # ImageField → faqat rasm ekanligini tekshiradi
    # FileExtensionValidator → kengaytmani tekshiradi

    def update(self, instance, validated_data):
        """
        Rasmni foydalanuvchiga biriktiradi.

        instance → joriy User obyekti
        validated_data → {'photo': <InMemoryUploadedFile>}
        """
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_DONE
            instance.save()
        return instance


# ============================================================
# 4. LoginSerializer — Tizimga kirish serialayzeri
# ============================================================
# Vazifasi:
#   - Telefon raqam YOKI email YOKI username qabul qiladi
#   - Parol bilan birgalikda tekshiradi
#   - Faqat to'liq ro'yxatdan o'tganlarni kiritadi
#   - JWT access va refresh token qaytaradi
# ============================================================

class LoginSerializer(TokenObtainPairSerializer):
    # TokenObtainPairSerializer → djangorestframework-simplejwt kutubxonasidan
    # JWT token yaratish imkonini beradi

    def __init__(self, *args, **kwargs):
        """
        Standart maydonlarga qo'shimcha maydonlar qo'shiladi.
        __init__ → obyekt yaratilganda bir marta chaqiriladi
        """
        super(LoginSerializer, self).__init__(*args, **kwargs)

        # 'userinput' → telefon/email/username ni qabul qiladi
        self.fields['userinput'] = serializers.CharField(required=True)

        # 'username' → ichki ishlatilinadi, foydalanuvchi kirmaydi
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        """
        Foydalanuvchi kim ekanligini aniqlaydi va tekshiradi.

        Jarayon:
        1. userinput ni tahlil qiladi (telefon/email/username)
        2. Bazadan foydalanuvchini topadi
        3. Ro'yxat holatini tekshiradi
        4. Django authenticate() orqali parolni tekshiradi
        """
        user_input = data.get('userinput')
        # Misol: '+998901234567', 'ali@mail.com', 'ali_123'

        if check_user_type(user_input) == 'username':
            # Username to'g'ridan ishlatiladi
            username = user_input

        elif check_user_type(user_input) == "email":
            # Email bo'yicha foydalanuvchi topiladi
            # email__iexact → katta/kichik harf farq qilmaydi
            # 'Ali@gmail.com' == 'ali@gmail.com' → True
            user = self.get_user(email__iexact=user_input)
            username = user.username
            # Email topildi → uning username si olinadi

        elif check_user_type(user_input) == 'phone':
            # Telefon raqam bo'yicha foydalanuvchi topiladi
            user = self.get_user(phone_number=user_input)
            username = user.username
            # Telefon topildi → uning username si olinadi

        else:
            data = {
                'success': True,
                'message': "Siz email, username yoki telefon raqami jonatishingiz kerak"
            }
            raise ValidationError(data)

        # username orqali foydalanuvchi topiladi
        current_user = User.objects.filter(username__iexact=username).first()

        if current_user is not None and current_user.auth_status in [NEW, CODE]:
            # Ro'yxatdan to'liq o'tmagan foydalanuvchi kira olmaydi!
            # NEW  → kod hali yuborilmagan
            # CODE → kod yuborilgan, lekin ma'lumotlar to'ldirilmagan
            raise ValidationError(
                {
                    'success': False,
                    'message': "Siz royhatdan toliq otmagansiz!"
                }
            )

        # Django'ning o'rnatilgan authenticate() funksiyasi:
        # username + password tekshiradi → to'g'ri bo'lsa User qaytaradi
        authentication_kwargs = {
            self.username_field: username,
            'password': data['password']
        }
        user = authenticate(**authentication_kwargs)

        if user is not None:
            self.user = user
            # Foydalanuvchi topildi → saqlanadi, validate() da ishlatiladi
        else:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Sorry, login or password you entered is incorrect. Please check and try again!"
                }
            )

    def validate(self, data):
        """
        auth_validate() dan keyin ishga tushadi.
        Foydalanuvchi holatini tekshirib token qaytaradi.
        """
        self.auth_validate(data)

        if self.user.auth_status not in [DONE, PHOTO_DONE]:
            # Faqat to'liq ro'yxatdan o'tganlar kirishlari mumkin
            raise PermissionDenied("Siz login qila olmaysiz. Ruxsatingiz yoq")

        data = self.user.token()
        # {"access": "jwt_token...", "refresh_token": "jwt_token..."}

        data['auth_status'] = self.user.auth_status
        # 'done' yoki 'photo_done'

        data['full_name'] = self.user.full_name
        # 'Ali Valiyev' (first_name + last_name)

        return data

    def get_user(self, **kwargs):
        """
        Berilgan filtri bo'yicha foydalanuvchini topadi.

        Misol:
        get_user(email__iexact='ali@mail.com')
        get_user(phone_number='+998901234567')
        """
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    "message": "No active account found"
                }
            )
        return users.first()


# ============================================================
# 5. LoginRefreshSerializer — Tokenni yangilash serialayzeri
# ============================================================
# Vazifasi:
#   - Access token muddati tugaganda yangilaydi
#   - Refresh token qabul qiladi
#   - Yangi access token qaytaradi
#   - Foydalanuvchining oxirgi kirish vaqtini yangilaydi
# ============================================================

class LoginRefreshSerializer(TokenRefreshSerializer):
    # TokenRefreshSerializer → simplejwt dan, refresh token tekshiradi

    def validate(self, attrs):
        """
        attrs → {'refresh': 'eyJ0eXAiO...'}

        Jarayon:
        1. Standart tekshiruv: refresh token haqiqiy va muddati o'tmaganmi
        2. Yangi access tokendan user_id olinadi
        3. Foydalanuvchi topiladi
        4. last_login yangilanadi
        """
        data = super().validate(attrs)
        # data = {'access': 'yangi_access_token...'}

        # Yangi access tokendan foydalanuvchi ID sini chiqarib olamiz
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']

        # Foydalanuvchini bazadan topamiz
        # get_object_or_404 → topilmasa avtomatik 404 xatosi
        user = get_object_or_404(User, id=user_id)

        # Foydalanuvchining oxirgi kirish vaqtini yangilaymiz
        # Birinchi argument None → signal yuborish shart emas
        update_last_login(None, user)

        return data


# ============================================================
# 6. LogoutSerializer — Tizimdan chiqish serialayzeri
# ============================================================
# Vazifasi:
#   - Refresh tokenni qabul qiladi
#   - View da bu token blacklist ga qo'shiladi
#   - Token endi hech qachon ishlatilmaydi
# ============================================================

class LogoutSerializer(serializers.Serializer):

    # Foydalanuvchi chiqishda refresh tokenini yuboradi
    refresh = serializers.CharField()
    # View da: RefreshToken(refresh).blacklist() chaqiriladi
    # Blacklist → token_blacklist app buni boshqaradi (settings.py da bor)


# ============================================================
# 7. ForgotPasswordSerializer — Parolni unutdim serialayzeri
# ============================================================
# Vazifasi:
#   - Telefon raqam yoki emailni qabul qiladi
#   - Bazadan foydalanuvchini topadi
#   - Topilgan foydalanuvchini validated_data ga qo'shadi
#   - View da yangi tasdiqlash kodi yuboriladi
# ============================================================

class ForgotPasswordSerializer(serializers.Serializer):

    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """
        Telefon yoki email bo'yicha foydalanuvchini topadi.

        Q() → SQL da OR operatori:
        WHERE phone_number='...' OR email='...'
        """
        email_or_phone = attrs.get('email_or_phone', None)

        if email_or_phone is None:
            raise ValidationError(
                {
                    "success": False,
                    'message': "Email yoki telefon raqami kiritilishi shart!"
                }
            )

        # Q() import: from django.db.models import Q
        # phone_number YOKI email bo'yicha qidiradi
        user = User.objects.filter(
            Q(phone_number=email_or_phone) | Q(email=email_or_phone)
        )

        if not user.exists():
            # Hech qanday foydalanuvchi topilmadi → 404
            raise NotFound(detail="User not found")

        # Topilgan foydalanuvchini attrs ga qo'shamiz
        # View da: serializer.validated_data.get('user') → User obyekti
        attrs['user'] = user.first()
        print(attrs)
        return attrs


# ============================================================
# 8. ResetPasswordSerializer — Yangi parol o'rnatish serialayzeri
# ============================================================
# Vazifasi:
#   - Yangi parol va tasdiqlash parolini qabul qiladi
#   - Ikkalasi mos kelishini tekshiradi
#   - Parolni xeshlaydi va saqlaydi
# ============================================================

class ResetPasswordSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(read_only=True)
    # Javobda id qaytariladi, lekin foydalanuvchi kirmaydi

    password = serializers.CharField(
        min_length=8,       # Minimum 8 belgi
        required=True,
        write_only=True     # Javobda ko'rinmaydi
    )

    confirm_password = serializers.CharField(
        min_length=8,
        required=True,
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'confirm_password'
        )

    def validate(self, data):
        """
        Ikki parolni solishtiradi va kuchliligini tekshiradi.
        """
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        # ⚠️ Eslatma: asl kodda confirm_password o'rniga password yozilgan edi
        # Bu tuzatilgan versiya

        if password != confirm_password:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Parollaringiz qiymati bir-biriga teng emas"
                }
            )

        if password:
            # Django parol kuchliligini tekshiradi
            validate_password(password)

        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        instance.set_password(password)
        instance.auth_status = DONE
        instance.save()
        return super(ResetPasswordSerializer, self).update(instance, validated_data)