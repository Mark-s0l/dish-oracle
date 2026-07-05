import logging
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView

from accounts.forms import ChangeEmailUser, EmailVerificationCode, ChangePasswordForm, SignUpUserForm
from accounts.models import CustomUser
from accounts.utils.cache_manager import CacheError, CacheManager
from accounts.utils.mailer import Mailer, MailerError
from django.contrib.auth import login

from accounts.tasks import send_registration_email_task

logger = logging.getLogger("accounts")

MAX_ATTEMPTS = 5

mailer = Mailer()


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    success_url = reverse_lazy("accounts:profile")
    template_name = "accounts/user_profile.html"
    form_class = ChangeEmailUser

    def get_object(self):
        return self.request.user


class ChangePasswordView(LoginRequiredMixin, FormView):
    form_class = ChangePasswordForm
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:verification_change_password")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        cache_manager = CacheManager(self.request.user.id)

        try:
            counter = cache_manager.cache_get(key="password_change_attempt")
        except CacheError:
            messages.info(
                self.request,
                "Произошла ошибка. Попробуйте позже",
            )
            return redirect("accounts:profile")
        attempt = counter["attempt"] if counter else 0
        attempt += 1
        if attempt > MAX_ATTEMPTS:
            messages.info(self.request, "Слишком много попыток, попробуйте позже")
            return redirect("accounts:profile")

        code = secrets.randbelow(1000000)
        code = str(code).zfill(6)
        hashed_code = make_password(code)
        hashed_password = make_password(form.cleaned_data["new_password1"])

        try:
            cache_manager.cache_set(
                "password_change",
                {
                    "hash": hashed_password,
                    "code": hashed_code,
                    "session_key": self.request.session.session_key,
                },
                timeout=300,
            )

            cache_manager.cache_set(
                "password_change_attempt", {"attempt": attempt}, timeout=3600
            )
        except CacheError:
            messages.info(
                self.request,
                "Произошла ошибка. Попробуйте позже",
            )
            return redirect("accounts:profile")

        try:
            mailer.send(
                subject="Подтверждение смены пароля",
                message=f"Ваш код: {code}",
                recipient_list=[self.request.user.email],
            )
        except MailerError:
            messages.info(self.request, "Ошибка отправки письма. Попробуйте позже")
            return redirect("accounts:profile")

        logger.info(f"[CHANGE_PASSWORD] User={
                self.request.user.id
                } started the password change procedure")

        return super().form_valid(form)


class VerificationChangePassword(LoginRequiredMixin, FormView):
    form_class = EmailVerificationCode
    template_name = "accounts/verification_email_code.html"
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        try:
            cache_manager = CacheManager(request.user.id)
            data = cache_manager.cache_get("password_change")
        except CacheError:
            messages.info(request, "Произошла ошибка. Попробуйте позже")
            return redirect("accounts:profile")
        if not data:
            messages.info(self.request, "Сессия истекла. Попробуйте еще раз")
            return redirect("accounts:change_password")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cache_manager = CacheManager(self.request.user.id)
        form_code = form.cleaned_data["code"]
        try:
            counter_attempt = cache_manager.cache_get("password_change_attempt")
            data = cache_manager.cache_get("password_change")
        except CacheError:
            messages.info(
                self.request,
                "Произошла ошибка. Попробуйте позже",
            )
            return redirect("accounts:profile")

        attempt = counter_attempt.get("attempt", 0) if counter_attempt else 0

        if attempt > MAX_ATTEMPTS:
            logger.info(
                f"[CHANGE_PASSWD] User={self.request.user.id} has exhausted the number of attempts"
            )
            messages.info(self.request, "Слишком много ошибок, попробуйте позже")

            try:
                mailer.send(
                    subject="Смена пароля",
                    message="Кто-то пытался сменить пароль много раз подряд безуспешно.",
                    recipient_list=[self.request.user.email],
                )
            except MailerError:
                logger.error(f"[CHANGE_PASSWORD] Сouldn't send a warning message for user={self.request.user.id}")
            
            cache_manager.cache_del("password_change")
            return redirect("accounts:profile")

        if not data:
            messages.info(self.request, "Сессия истекла. Попробуйте еще раз")
            return redirect("accounts:change_password")

        code = data["code"]
        hash_passwd = data["hash"]
        session_key = data["session_key"]

        if not check_password(form_code, code):
            attempt += 1
            try:
                cache_manager.cache_set(
                    "password_change_attempt", {"attempt": attempt}, timeout=3600
                )
            except CacheError:
                logger.error(f"[CHANGE_PASSWORD] Cache set error", exc_info=True)
                messages.info(self.request, "Произошла ошибка. Попробуйте позже")
                return redirect("accounts:profile")

            form.add_error(None, "Неверный код")
            return super().form_invalid(form)

        if self.request.session.session_key != session_key:
            messages.info(self.request, "Сессия истекла. Попробуйте еще раз")
            return super().form_invalid(form)

        self.request.user.password = hash_passwd
        self.request.user.save()
        update_session_auth_hash(self.request, self.request.user)
        cache_manager.cache_del("password_change")

        try:
            mailer.send(
                subject="Успешная смена пароля",
                message="Пароль на учетной записи успешно изменен. Если это делали не вы, пожалуйста ответьте на это письмо",
                recipient_list=[self.request.user.email],
            )
        except MailerError:
            logger.error(f"[CHANGE_PASSWD] Failed to send security notice user={self.request.user.id}")

        messages.info(self.request, "Пароль успешно изменен")
        logger.info(
            f"[CHANGE_PASSWORD] User={self.request.user.id} successfully changed the password"
        )
        return super().form_valid(form)


class SignUpUser(FormView):
    form_class = SignUpUserForm
    template_name = "accounts/sign_up_user.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="accounts.backends.EmailBackend")
        send_registration_email_task.delay(user.id, user.email)
        return super().form_valid(form)

