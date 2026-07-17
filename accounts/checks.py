from django.core.checks import Error, register
from accounts.utils.mailer import Mailer, MailerError

@register(deploy=True)
def check_smtp_connection(app_configs, **kwargs):
    errors = []
    try:
        Mailer.check_connection()
    except MailerError as e:
        errors.append(
            Error(
                str(e),
                hint="Check your SMTP settings in EMAIL_HOST / EMAIL_PORT",
                id="accounts.E001",
            )
        )
    return errors