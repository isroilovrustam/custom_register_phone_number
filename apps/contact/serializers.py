
from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)

    # Foydalanuvchi telefon raqami — faqat o'qish uchun

    class Meta:
        model = Contact
        fields = ('id', 'user_phone', 'subject', 'message', 'is_read', 'created_at')
        read_only_fields = ('id', 'user_phone', 'is_read', 'created_at')
        # Bu maydonlar foydalanuvchi tomonidan o'zgartirilmaydi


