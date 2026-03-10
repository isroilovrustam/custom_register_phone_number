from django.urls import path

from .views import (
    CreateUserView,        # 1. Ro'yxatdan o'tish
    VerifyAPIView,         # 2. Kodni tasdiqlash
    GetNewVerification,    # 3. Yangi kod olish
    ChangeUserInformationView,  # 4. Ma'lumotlarni to'ldirish
    ChangeUserPhotoView,   # 5. Rasm yuklash
    LoginView,             # 6. Tizimga kirish
    LoginRefreshView,      # 7. Tokenni yangilash
    LogoutView,            # 8. Chiqish
    ForgotPasswordView,    # 9. Parolni unutdim
    ResetPasswordView,     # 10. Parolni tiklash
)

urlpatterns = [
    # === RO'YXATDAN O'TISH BOSQICHLARI ===
    # Bosqich 1: Telefon raqam yuborish → kod keladi
    path('signup/', CreateUserView.as_view(), name='signup'),

    # Bosqich 2: Kelgan kodni tasdiqlash
    path('verify/', VerifyAPIView.as_view(), name='verify'),

    # Bosqich 2.1: Kod muddati o'tsa yangi kod olish
    path('new-verify/', GetNewVerification.as_view(), name='new-verify'),

    # Bosqich 3: Ism, familiya, username, parol to'ldirish
    path('change-user-information/', ChangeUserInformationView.as_view(), name='change-user-information'),

    # Bosqich 4: Rasm yuklash (ixtiyoriy, lekin to'liq ro'yxat uchun)
    path('change-user-photo/', ChangeUserPhotoView.as_view(), name='change-user-photo'),

    # === TIZIMGA KIRISH ===
    path('login/', LoginView.as_view(), name='login'),
    path('login/refresh/', LoginRefreshView.as_view(), name='login-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # === PAROLNI TIKLASH ===
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]