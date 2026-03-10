
from django.urls import path
from .views import ContactCreateView, ContactListView

urlpatterns = [
    # Yangi kontakt yuborish
    path('', ContactCreateView.as_view(), name='contact-create'),

    # O'zining kontaktlarini ko'rish
    path('my/', ContactListView.as_view(), name='contact-my-list'),
]