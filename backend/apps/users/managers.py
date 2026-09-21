from django.contrib.auth.models import BaseUserManager


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _criar(self, username, email, password, **extras):
        if not username:
            raise ValueError("O nome de usuario e obrigatorio.")
        if not email:
            raise ValueError("O e-mail e obrigatorio.")
        usuario = self.model(
            username=username, email=self.normalize_email(email), **extras
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, username, email=None, password=None, **extras):
        extras.setdefault("is_staff", False)
        extras.setdefault("is_superuser", False)
        extras.setdefault("tipo_usuario", "USUARIO")
        return self._criar(username, email, password, **extras)

    def create_superuser(self, username, email=None, password=None, **extras):
        extras.setdefault("is_staff", True)
        extras.setdefault("is_superuser", True)
        extras.setdefault("tipo_usuario", "ADMIN")
        if not extras["is_staff"] or not extras["is_superuser"]:
            raise ValueError("O superusuario precisa de is_staff e is_superuser.")
        return self._criar(username, email, password, **extras)

    def redacao(self):
        return self.filter(tipo_usuario__in=["ADMIN", "EDITOR", "JORNALISTA", "AUTOR"])
