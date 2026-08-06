import factory
from django.contrib.auth import get_user_model

Usuario = get_user_model()

PASSWORD_DE_PRUEBA = "ClaveSegura123"


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"usuario{n}")
    email = factory.Sequence(lambda n: f"usuario{n}@longbox.test")
    first_name = "Nombre"
    rol = "cliente"

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """La contraseña siempre se guarda hasheada, nunca en texto plano."""
        obj.set_password(extracted or PASSWORD_DE_PRUEBA)
        if create:
            obj.save()
