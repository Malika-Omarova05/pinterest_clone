from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Pin, ForbiddenTag


@receiver(post_save, sender=Pin)
def check_forbidden_tags(sender, instance, created, **kwargs):
    # Проверяем всегда (и при создании, и при обновлении)
    forbidden_tags = set(ForbiddenTag.objects.values_list('tag', flat=True).exclude(tag__exact=''))
    pin_tags = set(instance.tags.slugs())

    intersection = pin_tags.intersection(forbidden_tags)
    if intersection:
        # Если пин только что создан — удаляем его
        if created or instance.pk:
            instance.delete()
        raise ValidationError(
            _(f'Запрещённые теги: {", ".join(intersection)}. Пин не сохранён.')
        )