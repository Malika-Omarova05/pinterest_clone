from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ForbiddenTag(models.Model):
    tag = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.tag

class Pin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='pins/images/', null=True, blank=True)
    video = models.FileField(upload_to='pins/videos/', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager()

    def clean(self):
        if not self.image and not self.video:
            raise ValidationError(_('Нужно загрузить изображение или видео.'))

        # Убрали проверку тегов отсюда — она будет в сигнале

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Board(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    pins = models.ManyToManyField(Pin, related_name='boards')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.pins.count() < 2:
            raise ValidationError(_('Доска должна содержать минимум 2 пина.'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.full_clean()  # Проверка после сохранения M2M

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True, verbose_name="Отображаемое имя")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.display_name or self.user.username