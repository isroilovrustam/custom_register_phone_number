from django.utils import timezone
from rest_framework import permissions, status, generics
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from shared.utilis import send_email, send_phone_code
from .models import User, Confirmation, CODE, NEW, DONE, PHOTO_DONE
from .serializers import (
    SignUpSerializer,
    ChangeUserInformation,
    ChangeUserPhotoSerializer,
    LoginSerializer,
    LoginRefreshSerializer,
    LogoutSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)


class CreateUserView(generics.CreateAPIView):
    """
    Foydalanuvchi ro'yxatdan o'tishni boshlaydi.

    Jarayon:
    1. Telefon raqam qabul qilinadi
    2. Tekshiriladi (allaqachon bormi, formati to'g'rimi)
    3. Foydalanuvchi yaratiladi (auth_status='new')
    4. 4 xonali tasdiqlash kodi yaratiladi
    5. Kod emailga/SMS ga yuboriladi
    6. JWT tokenlar qaytariladi

    Ruxsat: Hamma (autentifikatsiya shart emas)
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)  # Hamma foydalana oladi
    serializer_class = SignUpSerializer


class VerifyAPIView(APIView):
    """
    Foydalanuvchiga yuborilgan 4 xonali kodni tasdiqlaydi.

    Jarayon:
    1. Token orqali foydalanuvchi aniqlanadi
    2. Yuborilgan kod bazadagi kod bilan taqqoslanadi
    3. Muddati o'tganmi tekshiriladi (2 daqiqa)
    4. To'g'ri bo'lsa: auth_status 'code' ga o'zgartiriladi
    5. Tasdiqlangan deb belgilanadi

    Ruxsat: Faqat login bo'lgan foydalanuvchi
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # So'rovdan kodni olamiz
        user = self.request.user
        code = request.data.get('code')

        # Bazadan foydalanuvchining kodini topamiz
        self.check_verify(user, code)

        return Response(
            data={
                "success": True,
                "auth_status": user.auth_status,
                "access": user.token()['access'],
                "refresh_token": user.token()['refresh_token']
            }
        )

    @staticmethod
    def check_verify(user, code):
        """
        Tasdiqlash kodini tekshiradi:
        - Kod bazada bormi?
        - Muddati o'tmaganmi?
        - Tasdiqlanmaganmi (faqat bir marta ishlatiladigan)?
        """
        verifies = user.confirmations.filter(
            expiration_time__gte=timezone.now(),  # Muddati o'tmagan
            is_confirmed=False,  # Hali tasdiqlanmagan
            code=code  # Kiritilgan kod
        ).order_by('-created_at')[:1]  # Faqat eng so'nggi birini olish
        if not verifies.exists():
            data = {
                "message": "Tasdiqlash kodingiz xato yoki muddati o'tgan!"
            }
            raise ValidationError(data)

        # Tasdiqlash kodi to'g'ri → tasdiqlangan deb belgilanadi
        verify = verifies.first()
        verify.is_confirmed = True
        verify.save()
        user.is_active = True  # Foydalanuvchini faollashtirish
        user.save()

        # Foydalanuvchi holati yangilanadi
        if user.auth_status == NEW:
            user.auth_status = CODE
            user.save()
        return True


class GetNewVerification(APIView):
    """
    Eski kod muddati o'tgan bo'lsa, yangi kod yuboradi.

    Jarayon:
    1. Foydalanuvchi aniqlanadi
    2. Avvalgi tasdiqlanmagan kodlar o'chiriladi
    3. Yangi kod yaratiladi
    4. Kod yana emailga/SMS ga yuboriladi

    Ruxsat: Faqat login bo'lgan foydalanuvchi
    """
    permission_classes = (permissions.IsAuthenticated,)

    # In GetNewVerification.check_verification:
    @staticmethod
    def check_verification(user):
        """
        Foydalanuvchi allaqachon to'liq ro'yxatdan o'tganmi tekshiradi.
        DONE yoki PHOTO_DONE bo'lsa → yangi kod kerak emas.
        """
        verifies = user.confirmations.filter(
            expiration_time__gte=timezone.now(),
            is_confirmed=False
        )
        if verifies.exists():
            data = {
                "message": "Kodingiz hali ham amal qilmoqda. Biroz kuting!"
            }
            raise ValidationError(data)

    # In GetNewVerification.get (add deletion of old unconfirmed codes for cleanup):
    def get(self, request, *args, **kwargs):
        user = self.request.user

        # Foydalanuvchi holati tekshiriladi
        self.check_verification(user)

        # Old unconfirmed codes cleanup (optional but good practice)
        user.confirmations.filter(is_confirmed=False).delete()

        # Yangi kod yaratib yuborish
        if user.phone_number:
            code = user.create_verify_code()
            send_email(user.phone_number, code)
            # send_phone_code(user.phone_number, code)  # SMS uchun

        return Response(
            {
                "success": True,
                "message": "Tasdiqlash kodingiz qayta yuborildi!"
            }
        )


class ChangeUserInformationView(generics.UpdateAPIView):
    """
    Foydalanuvchi kod tasdiqlangandan keyin ma'lumotlarini to'ldiradi.

    To'ldiriladigan maydonlar:
    - first_name (ism)
    - last_name (familiya)
    - username (foydalanuvchi nomi)
    - password (parol)
    - confirm_password (parolni tasdiqlash)

    auth_status 'code' → 'done' ga o'zgaradi.

    Ruxsat: Faqat login bo'lgan foydalanuvchi
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangeUserInformation
    http_method_names = ['put', 'patch']  # Faqat PUT va PATCH qabul qilinadi

    def get_object(self):
        """Joriy foydalanuvchini qaytaradi"""
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)
        data = {
            "success": True,
            "message": "Foydalanuvchi ma'lumotlari muvaffaqiyatli yangilandi",
            "auth_status": request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).partial_update(request, *args, **kwargs)
        data = {
            "success": True,
            "message": "Foydalanuvchi ma'lumotlari muvaffaqiyatli yangilandi",
            "auth_status": request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)


class ChangeUserPhotoView(APIView):
    """
    Foydalanuvchi profiliga rasm yuklaydi.

    Qo'llab-quvvatlangan formatlar: jpg, jpeg, png, heic, heif

    auth_status 'done' → 'photo_done' ga o'zgaradi.
    Ro'yxatdan o'tish to'liq yakunlanadi!

    Ruxsat: Faqat login bo'lgan foydalanuvchi
    """
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = ChangeUserPhotoSerializer(
            data=request.data
        )
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response(
                {
                    "message": "Rasm muvaffaqiyatli yuklandi!",
                    "auth_status": user.auth_status
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(generics.GenericAPIView):
    """
    Foydalanuvchi tizimga kiradi.

    Kiritish mumkin:
    - Telefon raqam + parol
    - Email + parol
    - Username + parol

    Qaytariladi:
    - access token (2 kun)
    - refresh token (15 kun)
    - auth_status
    - full_name

    MUHIM: Faqat auth_status='done' yoki 'photo_done' bo'lganda kirish mumkin!

    Ruxsat: Hamma
    """
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LoginRefreshView(TokenRefreshView):
    """
    Access token muddati tugaganda yangilaydi.

    Kerak: refresh token
    Qaytaradi: yangi access token

    Ruxsat: Hamma
    """
    serializer_class = LoginRefreshSerializer


class LogoutView(APIView):
    """
    Foydalanuvchini tizimdan chiqaradi.

    Jarayon:
    1. Refresh token qabul qilinadi
    2. Token "qora ro'yxat"ga (blacklist) qo'shiladi
    3. Token endi ishlatib bo'lmaydi

    Ruxsat: Faqat login bo'lgan foydalanuvchi
    """
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()  # Tokenni qora ro'yxatga qo'shish
            data = {
                "success": True,
                "message": "Siz tizimdan muvaffaqiyatli chiqdingiz"
            }
            return Response(data, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """
    Foydalanuvchi parolini unutganida yangilash kodi yuboradi.

    Jarayon:
    1. Telefon raqam yoki email qabul qilinadi
    2. Bazadan foydalanuvchi topiladi
    3. Yangi tasdiqlash kodi yaratiladi
    4. Kod emailga/SMS ga yuboriladi

    Ruxsat: Hamma
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validatsiyada topilgan foydalanuvchi
        user = serializer.validated_data.get('user')

        user.auth_status = NEW
        user.save()

        # Yangi tasdiqlash kodi yaratish
        if user.phone_number:
            code = user.create_verify_code()
            send_email(user.phone_number, code)
            # send_phone_code(user.phone_number, code)

        return Response(
            {
                "success": True,
                "message": "Tasdiqlash kodi yuborildi!",
                "access": user.token()['access'],
                "refresh_token": user.token()['refresh_token'],
            },
            status=status.HTTP_200_OK
        )


class ResetPasswordView(generics.UpdateAPIView):
    """
    Parolni unutdim kodini tasdiqlangandan keyin yangi parol o'rnatadi.

    Kerak:
    - password (yangi parol, minimum 8 belgi)
    - confirm_password (tasdiqlash)

    auth_status 'done' ga o'zgartiriladi.

    Ruxsat: Faqat login bo'lgan foydalanuvchi
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))
        except User.DoesNotExist:
            raise NotFound(detail="Foydalanuvchi topilmadi")
        return Response(
            {
                "success": True,
                "auth_status": user.auth_status,
                "message": "Parolingiz muvaffaqiyatli yangilandi!",
                "access": user.token()['access'],
                "refresh_token": user.token()['refresh_token'],
            }
        )
