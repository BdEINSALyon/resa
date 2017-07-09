import datetime

import requests
from django.contrib.auth import models as auth_models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from account import models as account_models


class AzureGroup(models.Model):
    group = models.ForeignKey(auth_models.Group, related_name='azure_groups')
    azure_id = models.CharField(max_length=100, choices=())
    azure_name = models.CharField(max_length=250, blank=True)

    def check_user(self, user):
        token = account_models.OAuthToken.objects.filter(user=user, service__name='microsoft').last()
        if token is None:
            return False

        if datetime.datetime.now() > token.auth_token_expiration:
            from account.models import OAuthService
            ms = OAuthService.objects.filter(name='microsoft').first().provider
            ms.refresh_token(token)

        from account.providers import MicrosoftOAuthProvider
        result = requests.post(MicrosoftOAuthProvider.graph('/me/checkMemberGroups'), json={
            'groupIds': [self.azure_id]
        }, headers={
            'Authorization': 'Bearer {}'.format(token.auth_token)
        })
        if result.status_code < 300:
            return self.azure_id in result.json()['value']
        else:
            return False

    def __str__(self):
        return '{} -> {}'.format(self.azure_name, self.group)


class User(AbstractUser):
    """
    Represents a user in our app.
    I implemented this class because I needed a custom behavior for is_staff and is_superuser.
    This class also fetches Azure groups whenever it's needed so the user's permissions
    are kept up to date.
    """

    _is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    _is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_(
            'Designates that this user has all permissions without '
            'explicitly assigning them.'
        ),
    )

    last_fetched_groups = models.DateTimeField(default=None, null=True, blank=True,
                                               help_text='If older than 5 min, groups will be fetched from Azure '
                                                         'next time the user makes a request.')

    def __init__(self, *args, **kwargs):
        self._is_staff = kwargs.get('is_staff', False)
        self._is_superuser = kwargs.get('is_superuser', False)
        super().__init__(*args, **kwargs)

        if self.id:
            if not self.last_fetched_groups \
                    or timezone.now() > self.last_fetched_groups + datetime.timedelta(minutes=5):

                for group in auth_models.Group.objects.all():
                    res = False
                    for g in group.azure_groups.all():
                        res |= g.check_user(self)

                    if res:
                        self.save()
                        group.save()
                        self.groups.add(group)
                    else:
                        self.save()
                        group.save()
                        self.groups.remove(group)

                self.last_fetched_groups = timezone.now()
                self.save()

    @property
    def is_staff(self):
        return self._is_staff or self.groups.filter(name__icontains='admin').exists()

    @is_staff.setter
    def is_staff(self, is_staff):
        self._is_staff = is_staff

    @property
    def is_superuser(self):
        return self._is_superuser or self.groups.filter(name__icontains='admin').exists()

    @is_superuser.setter
    def is_superuser(self, is_superuser):
        self._is_superuser = is_superuser
