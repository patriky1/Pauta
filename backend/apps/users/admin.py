from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "nome", "email", "tipo_usuario", "is_active", "date_joined")
    list_filter = ("tipo_usuario", "is_active", "is_staff")
    search_fields = ("username", "nome", "email")
    ordering = ("nome",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Perfil", {"fields": ("nome", "email", "foto", "biografia")}),
        ("Redes", {"fields": ("site", "twitter", "instagram", "linkedin")}),
        ("Permissoes", {"fields": ("tipo_usuario", "is_active", "is_staff",
                                   "is_superuser", "groups", "user_permissions")}),
        ("Moderacao", {"fields": ("bloqueado_em", "motivo_bloqueio")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "nome", "email", "tipo_usuario",
                       "password1", "password2"),
        }),
    )
