from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from user.models import DONE, PHOTO_DONE
from .models import Contact
from .serializers import ContactSerializer


class IsFullyRegistered(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.auth_status in [DONE, PHOTO_DONE]
        )


class ContactCreateView(generics.CreateAPIView):
    """
    Foydalanuvchi kontakt (murojaat) yuboradi.

    URL: POST /api/v1/contacts/

    Kerak (JSON):
    {
        "subject": "Muammo haqida",
        "message": "Mening muammom..."
    }

    Qaytaradi: Yaratilgan kontakt ma'lumotlari

    RUXSAT: Faqat to'liq ro'yxatdan o'tgan foydalanuvchilar!
    (auth_status = 'done' yoki 'photo_done')
    """
    serializer_class = ContactSerializer
    permission_classes = [IsFullyRegistered]

    def perform_create(self, serializer):
        # Kontaktga avtomatik joriy foydalanuvchini biriktiramiz
        serializer.save(user=self.request.user)


class ContactListView(generics.ListAPIView):
    """
    Joriy foydalanuvchining barcha murojaat ro'yxatini ko'rish.

    URL: GET /api/v1/contacts/my/

    Faqat O'ZI yuborgan kontaktlarni ko'radi.

    RUXSAT: Faqat to'liq ro'yxatdan o'tgan foydalanuvchilar!
    """
    serializer_class = ContactSerializer
    permission_classes = [IsFullyRegistered]

    def get_queryset(self):
        # Faqat joriy foydalanuvchining kontaktlari
        return Contact.objects.filter(user=self.request.user).order_by('-created_at')


