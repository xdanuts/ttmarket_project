from django.db.models.signals import pre_save
from helpers.emails import send_register_email
from store.models import MyUserManager, MyUser


def generate_random_password(sender, instance, *args, **kwargs):
    if not instance.pk:
        email = instance.email
        first_name = instance.first_name
        last_name = instance.last_name

        generated_password = MyUserManager().make_random_password()
        send_register_email(first_name, last_name, email, generated_password)

        instance.set_password(generated_password)


pre_save.connect(generate_random_password, sender=MyUser)
