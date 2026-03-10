from django.urls import path, include

urlpatterns = [
    # Foydalanuvchi endpointlari
    path('v1/users/', include('user.urls')),

    # Kontakt endpointlari (faqat ro'yxatdan o'tganlar)
    path('v1/contacts/', include('contact.urls')),
]