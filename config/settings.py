from datetime import timedelta
from pathlib import Path
import sys
import os
from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# PYTHON PATH GA APPS PAPKASINI QO'SHISH
# ============================================================
# Nima uchun kerak?
# apps/ papkasi ichida user, shared, contact modullari bor.
# Django ularni to'g'ridan import qila olmaydi.
# sys.path.append() → Python qidiruv yo'liga qo'shiladi.
# Shundan keyin: from user.models import User → ishlaydi
sys.path.append(os.path.join(BASE_DIR, 'apps'))

# ============================================================
# MUHIT O'ZGARUVCHILARI (.env fayl)
# ============================================================
# .env fayl — maxfiy ma'lumotlar saqlanadigan fayl
# GitHub ga HECH QACHON yuklanmaydi! (.gitignore ga qo'shiladi)
#
# .env fayl namunasi:
# SECRET_KEY=django-insecure-xxxxxxxxxxxxxxxxxxx
# DEBUG=True
# DB_NAME=mydb
# DB_USER=postgres
# DB_PASSWORD=secret123
# DB_HOST=localhost
# DB_PORT=5432
# EMAIL_HOST=smtp.gmail.com
# EMAIL_HOST_USER=myemail@gmail.com
# EMAIL_HOST_PASSWORD=app_password
# account_sid=ACxxxxxxxxxxxxxxxx
# auth_token=xxxxxxxxxxxxxxxx

# ============================================================
# MAXFIY KALIT (SECRET_KEY)
# ============================================================
# Django ning kriptografik asosi — sessiyalar, tokenlar, parollar uchun ishlatiladi
# HECH QACHON ochiq qoldirilmasin!
# Ishlab chiqarishda (production) har doim .env dan olinsin
SECRET_KEY = config('SECRET_KEY')

# ============================================================
# DEBUG REJIMI
# ============================================================
# DEBUG=True  → Ishlab chiqish (development) rejimi:
#   - Xatolar ekranda to'liq ko'rinadi
#   - Static fayllar avtomatik topiladi
#   - Tezroq ishlab chiqish imkoni
#
# DEBUG=False → Ishlab chiqarish (production) rejimi:
#   - Xato tafsilotlari yashiriladi (xavfsizlik!)
#   - Static fayllar alohida serve qilinadi
#   - ALLOWED_HOSTS to'liq ko'rsatilishi SHART
#
# ✅ TUZATILDI: cast=bool → .env dagi 'True' stringini haqiqiy True ga o'giradi
DEBUG = config('DEBUG', default=True, cast=bool)

# ============================================================
# RUXSAT ETILGAN HOSTLAR (ALLOWED_HOSTS)
# ============================================================
# Qaysi domenlardan so'rov qabul qilinadi.
#
# ❌ KAMCHILIK: ["*"] → barcha domenlardan qabul qiladi
#    Bu ishlab chiqarishda XAVFLI! HTTP Host header hujumlariga yo'l ochadi
#
# ✅ TUZATILDI:
#    Development da: ["*"] yoki ["localhost", "127.0.0.1"]
#    Production da:  ["mysite.uz", "www.mysite.uz"]
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')
# .env da: ALLOWED_HOSTS=mysite.uz,www.mysite.uz
# Bu satrni split(',') bilan ro'yxatga o'giradi

# ============================================================
# O'RNATILGAN ILOVALAR (INSTALLED_APPS)
# ============================================================
INSTALLED_APPS = [
    # --- Django o'rnatilgan ilovalar ---
    'django.contrib.admin',        # Admin panel → /admin/
    'django.contrib.auth',         # Foydalanuvchi tizimi (login/logout)
    'django.contrib.contenttypes', # Model turlari bilan ishlash
    'django.contrib.sessions',     # Sessiya (cookie) boshqaruvi
    'django.contrib.messages',     # Flash xabarlar (success, error)
    'django.contrib.staticfiles',  # CSS, JS, rasm fayllarini boshqarish

    # --- Uchinchi tomon kutubxonalar ---
    'rest_framework',                        # Django REST Framework — API yaratish
    'rest_framework.authtoken',              # Token autentifikatsiya (DRF)
    'rest_framework_simplejwt',              # JWT token yaratish va tekshirish
    'rest_framework_simplejwt.token_blacklist', # Logout uchun token o'chirish (blacklist)
    'drf_yasg',                              # Swagger/ReDoc — API dokumentatsiya

    # ✅ QO'SHILDI: corsheaders — Frontend (React/Vue) bilan ishlash uchun
    # pip install django-cors-headers
    'corsheaders',

    # --- Bizning ilovalar ---
    'user',     # Foydalanuvchi tizimi
    'shared',   # Umumiy modellar va funksiyalar
    'contact',  # Murojaat tizimi
]

# ============================================================
# MIDDLEWARE (O'rta dasturlar)
# ============================================================
# Har bir HTTP so'rov ushbu zanjirdan o'tadi (yuqoridan pastga)
# Har bir HTTP javob teskari tartibda o'tadi (pastdan yuqoriga)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Xavfsizlik: HTTPS yo'naltirish, XSS himoya, HSTS sarlavhalari

    # ✅ QO'SHILDI: CorsMiddleware — SecurityMiddleware dan KEYIN bo'lishi shart
    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    # Sessiyalarni boshqaradi: foydalanuvchi ma'lumotlarini brauzerda saqlash

    'django.middleware.common.CommonMiddleware',
    # URL normalizatsiya: /about → /about/ avtomatik yo'naltirish

    'django.middleware.csrf.CsrfViewMiddleware',
    # CSRF himoya: Soxta so'rovlardan himoya (Cross-Site Request Forgery)
    # API uchun odatda o'chiriladi yoki SessionAuthentication ishlatmasa kerak emas

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # request.user ni to'ldiradi: kim so'rov yuborayotganini aniqlaydi

    'django.contrib.messages.middleware.MessageMiddleware',
    # Flash xabarlarni boshqaradi (bir martalik xabarlar)

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Clickjacking himoya: saytni iframe ichida ko'rsatishdan himoya
]

# ============================================================
# URL KONFIGURATSIYA
# ============================================================
# Barcha URL yo'naltirish shu fayldan boshlanadi
ROOT_URLCONF = 'config.urls'

# ============================================================
# SHABLONLAR (TEMPLATES)
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DjangoTemplates → Django ning o'z shablon tizimi

        'DIRS': [BASE_DIR / 'templates'],
        # Qo'shimcha shablon papkasi → /project/config/templates/
        # Bizda: email/authentication/activate_account.html shu yerda

        'APP_DIRS': True,
        # True → har bir app ning templates/ papkasini avtomatik qidiradi
        # Masalan: user/templates/ papkasi ham tekshiriladi

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                # request obyektini shablonga uzatadi → {{ request.user }}

                'django.contrib.auth.context_processors.auth',
                # user va perms ni shablonga uzatadi → {{ user.username }}

                'django.contrib.messages.context_processors.messages',
                # flash xabarlarni shablonga uzatadi → {% for msg in messages %}
            ],
        },
    },
]

# ============================================================
# WSGI/ASGI KONFIGURATSIYA
# ============================================================
# WSGI → Web Server Gateway Interface (sinxron server)
# Nginx, Gunicorn bilan ishlatiladi
WSGI_APPLICATION = 'config.wsgi.application'

# ============================================================
# MA'LUMOTLAR BAZASI (DATABASE)
# ============================================================
# ❌ KAMCHILIK: SQLite faqat development uchun yaxshi
#    Production da PostgreSQL ishlatish TAVSIYA ETILADI
#    SQLite: bitta fayl, parallel so'rovlarda muammo, katta loyiha uchun mo'lmas
#
# ✅ TUZATILDI: .env dan PostgreSQL sozlamalari o'qiladi
#    Development: SQLite (tez va oson)
#    Production: PostgreSQL (ishonchli va kuchli)

if DEBUG:
    # Development: SQLite (sozlash shart emas)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production: PostgreSQL
    # pip install psycopg2-binary
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# ============================================================
# PAROL TEKSHIRUVLARI (AUTH_PASSWORD_VALIDATORS)
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # Parol foydalanuvchi ma'lumotlariga o'xshab ketmasin
        # Masalan: username='ali123', password='ali123' → xato!
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        # Minimum uzunlik tekshiruvi
        # ✅ QO'SHILDI: min_length → 8 (standart 8, ko'paytirish mumkin)
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # Keng tarqalgan parollarni bloklaydi
        # '123456', 'password', 'qwerty' kabilar → xato!
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # Faqat raqamdan iborat parolni bloklaydi
        # '12345678' → xato!
    },
]

# ============================================================
# TIL VA VAQT MINTAQASI
# ============================================================
LANGUAGE_CODE = 'uz'
# ✅ TUZATILDI: 'en-us' → 'uz' (O'zbek tili)
# Admin panel va tizim xabarlari o'zbek tilida bo'ladi

TIME_ZONE = 'Asia/Tashkent'
# Toshkent vaqti: UTC+5
# timezone.now() → Toshkent vaqtini qaytaradi

USE_I18N = True
# Internationalization → ko'p tilli qo'llab-quvvatlash yoqilgan

USE_TZ = True
# True → barcha vaqtlar UTC da saqlanadi, TIME_ZONE ga ko'ra ko'rsatiladi
# MUHIM: Confirmation.expiration_time tekshiruvi to'g'ri ishlashi uchun True bo'lishi SHART

# ============================================================
# STATIC VA MEDIA FAYLLAR
# ============================================================

# Static fayllar — CSS, JavaScript, rasmlar (kod bilan keladi)
STATIC_URL = '/static/'
# URL manzil: http://localhost:8000/static/style.css

STATICFILES_DIRS = [
    BASE_DIR / 'static',
    # Development da qo'shimcha static papka
    # /project/config/static/ papkasidagi fayllar ham topiladi
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
# python manage.py collectstatic → barcha static fayllar shu yerga yig'iladi
# Production da Nginx bu papkadan fayllarni beradi

# Media fayllar — Foydalanuvchi yuklaydigan fayllar (rasmlar, hujjatlar)
MEDIA_URL = '/media/'
# URL manzil: http://localhost:8000/media/user/photos/avatar.jpg

MEDIA_ROOT = BASE_DIR / 'media'
# Fayllar diskda shu papkaga saqlanadi: /project/config/media/

# ============================================================
# BIRLAMCHI AVTOMATIK MAYDON
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Modellardagi id maydoni uchun standart tur
# BigAutoField → 64-bit integer (9 kvintillion gacha)
# Katta loyihalarda AutoField (32-bit) chekloviga yetib qolmaslik uchun

# ============================================================
# MAXSUS FOYDALANUVCHI MODELI
# ============================================================
AUTH_USER_MODEL = 'user.User'
# Django ning standart User o'rniga bizning User ishlatiladi
# user/models.py dagi class User(AbstractUser, BaseModel) → shu!
# MUHIM: Loyiha boshida belgilanishi SHART, keyinroq o'zgartirish qiyin

# ============================================================
# EMAIL SOZLAMALARI
# ============================================================

if DEBUG:
    # Development: Emaillar brauzer consolega chiqadi (yuborilmaydi)
    # Terminal da ko'rish mumkin: python manage.py runserver
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # ✅ QO'SHILDI: Production da haqiqiy email yuborish
    # pip install django → EmailMessage ishlatiladi
    # Gmail uchun: "App Passwords" yaratish kerak (2FA yoqilgan bo'lsa)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = True
    # TLS (Transport Layer Security) → shifrlangan ulanish
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    # Yuboruvchi email: myapp@gmail.com
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    # Gmail App Password (oddiy parol emas!)
    DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')
    # Kimdan ko'rinishi: myapp@gmail.com

# ============================================================
# REST FRAMEWORK SOZLAMALARI
# ============================================================
REST_FRAMEWORK = {
    # Standart ruxsat: Faqat login bo'lgan foydalanuvchilar
    # View da permission_classes = (permissions.AllowAny,) bilan o'zgartiriladi
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Autentifikatsiya usullari (ikkalasi ham tekshiriladi)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # DRF Token: "Token abc123..." sarlavha bilan
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # JWT Token: "Bearer eyJ..." sarlavha bilan (biz ishlatamiz)
    ],

    # ✅ QOSHILDI: Xato javoblar formati
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    # ✅ QOSHILDI: Sana/vaqt formati
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

# ============================================================
# JWT TOKEN SOZLAMALARI (SIMPLE_JWT)
# ============================================================
SIMPLE_JWT = {
    # --- Token muddatlari ---
    'ACCESS_TOKEN_LIFETIME': timedelta(days=2),
    # Access token → 2 kun amal qiladi
    # Har bir API so'rovda ishlatiladi

    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
    # Refresh token → 15 kun amal qiladi
    # Faqat yangi access token olish uchun

    # --- Rotation (aylanish) ---
    'ROTATE_REFRESH_TOKENS': False,
    # False → Har refresh da yangi refresh token BERILMAYDI
    # True  → Har refresh da yangi refresh token ham beriladi (xavfsizroq)

    'BLACKLIST_AFTER_ROTATION': False,
    # False → Eski refresh token blacklist ga tushMaydi
    # True  → ROTATE_REFRESH_TOKENS=True bilan birga ishlatiladi
    # Ikkalasini True qilish tavsiya etiladi xavfsizlik uchun

    'UPDATE_LAST_LOGIN': False,
    # False → Token olishda last_login yangilanMAYDI
    # True  → login qilinganda last_login yangilanadi (foydali)
    # ✅ LoginRefreshSerializer da qo'lda update_last_login() chaqirilgan

    # --- Kriptografiya ---
    'ALGORITHM': 'HS256',
    # HMAC-SHA256 algoritmi — tez va ishonchli
    # RS256 (RSA) → ochiq/yopiq kalit juftligi bilan (murakkabro'q)

    'SIGNING_KEY': config('SECRET_KEY'),
    # Token imzolash kaliti → Django SECRET_KEY dan foydalaniladi
    # ✅ TUZATILDI: SECRET_KEY o'zgaruvchisidan olinadi

    'VERIFYING_KEY': '',
    # RS256 uchun ochiq kalit → HS256 da bo'sh qoladi

    'AUDIENCE': None,       # Token kimga mo'ljallangan (ixtiyoriy)
    'ISSUER': None,         # Token kim tomonidan berilgan (ixtiyoriy)
    'JSON_ENCODER': None,   # Maxsus JSON encoder (odatda kerak emas)
    'JWK_URL': None,        # JSON Web Key URL (ixtiyoriy)
    'LEEWAY': 0,
    # Muddatni tekshirishda vaqt farqiga ruxsat (soniyalarda)
    # 0 → hech qanday farqqa ruxsat yo'q
    # 10 → 10 soniya kechikishga ruxsat (server vaqt farqi uchun)

    # --- Sarlavha sozlamalari ---
    'AUTH_HEADER_TYPES': ('Bearer',),
    # Authorization: Bearer eyJ... → "Bearer" so'zi kerak
    # Agar 'JWT' qo'shsak: Authorization: JWT eyJ... ham ishlaydi

    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    # Django da HTTP sarlavha nomi: HTTP_ prefiksi qo'shiladi
    # Brauzerdan: Authorization: Bearer ...
    # Django ichida: HTTP_AUTHORIZATION

    # --- Foydalanuvchi identifikatsiyasi ---
    'USER_ID_FIELD': 'id',
    # Token ichiga qaysi maydon saqlanadi
    # Bizning User modelida: id = UUID (BaseModel dan)

    'USER_ID_CLAIM': 'user_id',
    # Token ichidagi kalit nomi: {"user_id": "uuid..."}
    # LoginRefreshSerializer da: access_token_instance['user_id']

    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    # Foydalanuvchi faolmi tekshirish: user.is_active → True bo'lishi kerak

    # --- Token turlari ---
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    # Qaysi token sinfi ishlatiladi → AccessToken

    'TOKEN_TYPE_CLAIM': 'token_type',
    # Token ichida turi saqlanadi: {"token_type": "access"}

    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    # Tokendan foydalanuvchi olish uchun sinf

    'JTI_CLAIM': 'jti',
    # JWT ID → har bir token uchun noyob identifikator
    # Blacklist da tokenni aniqlash uchun ishlatiladi: {"jti": "unique-id"}

    # --- Sliding token (kamdan-kam ishlatiladi) ---
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),

    # --- Standart serialayzerlar ---
    # ✅ TUZATILDI: Bizning custom serialayzerlar ko'rsatildi
    'TOKEN_OBTAIN_SERIALIZER': 'user.serializers.LoginSerializer',
    # login/ → LoginSerializer ishlatiladi

    'TOKEN_REFRESH_SERIALIZER': 'user.serializers.LoginRefreshSerializer',
    # login/refresh/ → LoginRefreshSerializer ishlatiladi

    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
    'SLIDING_TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer',
    'SLIDING_TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer',
}

# ============================================================
# CORS SOZLAMALARI (Frontend bilan ishlash)
# ✅ YANGI QO'SHILDI: django-cors-headers
# pip install django-cors-headers
# ============================================================
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    # Development da barcha domenlardan so'rov qabul qilinadi
else:
    CORS_ALLOWED_ORIGINS = [
        'https://mysite.uz',
        'https://www.mysite.uz',
        # Frontend domenlarini shu yerga qo'shing
    ]

CORS_ALLOW_CREDENTIALS = True
# Cookie va Authorization sarlavhasini yuborish imkoni

CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',   # Bearer token uchun
    'content-type',
    'origin',
    'x-requested-with',
]