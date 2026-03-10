from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    # Yozuv yaratilgan vaqt — avtomatik to'ldiriladi

    updated_at = models.DateTimeField(auto_now=True)

    # Yozuv yangilangan vaqt — har saqlashda avtomatik yangilanadi

    class Meta:
        abstract = True
        # Bu model mustaqil jadval yaratmaydi,
        # faqat boshqa modellarga meros berish uchun