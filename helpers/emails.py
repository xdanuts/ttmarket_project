from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.conf import settings
from django.template.loader import get_template
from django.shortcuts import reverse
from django.contrib.sites.models import Site


def send_register_email(first_name, last_name, email, password):
    login_url = '{HOST}{LOGIN_ROUTE}'.format(
        HOST=Site.objects.get_current().domain,
        LOGIN_ROUTE=reverse('signin_view')
    )
    email_template = get_template('emails/register.html')
    email_content = email_template.render({
        'password': password,
        'first_name': first_name,
        'last_name': last_name,
        'login_url': login_url,
    })

    mail = EmailMultiAlternatives(
        'New account',
        email_content,
        settings.EMAIL_HOST_USER,
        [email]
    )
    mail.content_subtype = 'html'
    mail.send()
