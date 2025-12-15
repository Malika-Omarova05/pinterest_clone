from django.contrib import admin
from .models import Pin, Board, Profile, ForbiddenTag
from django.utils.translation import gettext_lazy as _

admin.site.site_header = 'Админ-панель Pinterest Clone'
admin.site.site_title = 'Админ Pinterest'
admin.site.index_title = 'Добро пожаловать в админ-панель'

@admin.register(ForbiddenTag)
class ForbiddenTagAdmin(admin.ModelAdmin):
    list_display = ('tag',)
    search_fields = ('tag',)

@admin.register(Pin)
class PinAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('user', 'created_at')

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')
    search_fields = ('user__username',)