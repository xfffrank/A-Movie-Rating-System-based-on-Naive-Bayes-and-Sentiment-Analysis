from django.contrib.auth import forms
from django.contrib.auth.models import User
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()

class RegisterForm(forms.UserCreationForm):

    class Meta(forms.UserCreationForm.Meta):
        model = User
        fields = {"username", "email"}

from django import forms
# class PasswordResetForm(forms.Form):
#     error_messages = {
#         'unknown': ("That email address doesn't have an associated "
#                      "user account. Are you sure you've registered?"),
#         'unusable': ("The user account associated with this email "
#                       "address cannot reset the password."),
#         }
#     def clean_email(self):
#         """
#         Validates that an active user exists with the given email address.
#         """
#         UserModel = get_user_model()
#         email = self.cleaned_data["email"]
#         self.users_cache = UserModel._default_manager.filter(email__iexact=email)
#         if not len(self.users_cache):
#             raise forms.ValidationError(self.error_messages['unknown'])
#         if not any(user.is_active for user in self.users_cache):
#             # none of the filtered users are active
#             raise forms.ValidationError(self.error_messages['unknown'])
#         # if any((user.password == UNUSABLE_PASSWORD)
#         #     for user in self.users_cache):
#         #     raise forms.ValidationError(self.error_messages['unusable'])
#         return email
#
#     def save(self, domain_override=None,
#              subject_template_name='registration/password_reset_subject.txt',
#              email_template_name='registration/password_reset_email.html',
#              use_https=False, token_generator=default_token_generator,
#              from_email=None, request=None):
#         """
#         Generates a one-use only link for resetting password and sends to the
#         user.
#         """
#         from django.core.mail import send_mail
#         for user in self.users_cache:
#             if not domain_override:
#                 current_site = get_current_site(request)
#                 site_name = current_site.name
#                 domain = current_site.domain
#             else:
#                 site_name = domain = domain_override
#             c = {
#                 'email': user.email,
#                 'domain': domain,
#                 'site_name': site_name,
#                 # 'uid': int_to_base36(user.pk),
#                 'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
#                 'user': user,
#                 'token': token_generator.make_token(user),
#                 'protocol': use_https and 'https' or 'http',
#                 }
#             subject = loader.render_to_string(subject_template_name, c)
#             # Email subject *must not* contain newlines
#             subject = ''.join(subject.splitlines())
#             email = loader.render_to_string(email_template_name, c)
#             send_mail(subject, email, from_email, [user.email])



class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')


        email_message.send()

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        active_users = UserModel._default_manager.filter(**{
            '%s__iexact' % UserModel.get_email_field_name(): email,
            'is_active': True,
        })
        return (u for u in active_users if u.has_usable_password())

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]


        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )