import re
import threading
from django.core.mail import EmailMessage
import phonenumbers
from decouple import config
from phonenumbers import NumberParseException
from twilio.rest import Client
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

# === REGEX SHABLONLAR ===
email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
# Email formatini tekshirish uchun: test@gmail.com ✓

phone_regex = re.compile(r"(\+[0-9]+\s*)?(\([0-9]+\))?[\s0-9\-]+[0-9]+")
# Telefon raqam formatini tekshirish uchun: +998901234567 ✓

username_regex = re.compile(r"^[a-zA-Z0-9_.-]+$")
# Username formatini tekshirish uchun: ali_123 ✓


# === FUNKSIYA 1: Telefon raqamni tekshirish ===
def check_phone_number(phone_number):
    """
    Kiritilgan telefon raqam to'g'ri formatdami yoki yo'qligini tekshiradi.
    To'g'ri bo'lsa → 'phone' qaytaradi
    Noto'g'ri bo'lsa → ValidationError chiqaradi
    """
    try:
        phone_number = phonenumbers.parse(phone_number, None)
        if phonenumbers.is_valid_number(phone_number):
            return "phone"
    except NumberParseException:
        pass

    data = {
        "success": False,
        "message": "Telefon raqamingiz noto'g'ri"
    }
    raise ValidationError(data)


# === FUNKSIYA 2: Foydalanuvchi kiritgan ma'lumot turini aniqlash ===
def check_user_type(user_input):
    """
    Login qilishda foydalanuvchi nima kiritganini aniqlaydi:
    - Email kiritdimi? → 'email' qaytaradi
    - Telefon raqam kiritdimi? → 'phone' qaytaradi
    - Username kiritdimi? → 'username' qaytaradi
    - Hech biri emas → ValidationError
    """
    if re.fullmatch(email_regex, user_input):
        user_input = 'email'
    elif re.fullmatch(phone_regex, user_input):
        user_input = 'phone'
    elif re.fullmatch(username_regex, user_input):
        user_input = 'username'
    else:
        data = {
            "success": False,
            "message": "Email, username yoki telefon raqamingiz noto'g'ri"
        }
        raise ValidationError(data)
    return user_input


# === SINF: Email yuborish uchun alohida thread (ip) ===
class EmailThread(threading.Thread):
    """
    Emailni asosiy dastur kutmasdan, orqa fonda yuboradi.
    Foydalanuvchi email yuborilishini kutmaydi → tizim tezroq ishlaydi.
    """
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()  # Email yuborish


# === SINF: Email obyektini yaratish ===
class Email:
    @staticmethod
    def send_email(data):
        """
        Email xabarini yaratadi va EmailThread orqali yuboradi.
        data = {
            'subject': 'Sarlavha',
            'body': 'Matn yoki HTML',
            'to_email': 'kimga@gmail.com',
            'content_type': 'html'  # ixtiyoriy
        }
        """
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data.get('content_type') == "html":
            email.content_subtype = 'html'  # HTML formatda yuboradi
        EmailThread(email).start()  # Orqa fonda yuborish boshlanadi


# === FUNKSIYA 3: Tasdiqlash kodi emailga yuborish ===
def send_email(email, code):
    """
    Ro'yxatdan o'tishda tasdiqlash kodini email orqali yuboradi.
    HTML shablon ishlatiladi: activate_account.html
    """
    html_content = render_to_string(
        'email/authentication/activate_account.html',
        {"code": code}  # Shablonga kod uzatiladi
    )
    Email.send_email(
        {
            "subject": "Royhatdan otish",
            "to_email": email,
            "body": html_content,
            "content_type": "html"
        }
    )


# === FUNKSIYA 4: Tasdiqlash kodi SMS yuborish (Twilio) ===
def send_phone_code(phone, code):
    """
    Twilio xizmati orqali telefon raqamga SMS yuboradi.
    Hozirda izohda (# belgisi bilan), ya'ni ishlatilmayapti.
    account_sid va auth_token → .env faylidan olinadi (maxfiy kalitlar)
    """
    account_sid = config('account_sid')
    auth_token = config('auth_token')
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=f"Salom do'stim! Sizning tasdiqlash kodingiz: {code}\n",
        from_="+99899325242",
        to=f"{phone}"
    )