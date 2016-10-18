from authentication.views import password_change_done
from django.conf.urls import url
from django.contrib.auth.views import login, logout, password_change
from resa.settings import LOGOUT_REDIRECT_URL

urlpatterns = [
    url(
        r'^login/$',
        login,
        {
            'template_name': 'authentication/auth_form.html',
            'extra_context': {
                'title': 'Connexion',
                'action': 'Connexion'
            }
        },
        name='login'
    ),
    url(
        r'^logout/$',
        logout,
        {'next_page': LOGOUT_REDIRECT_URL},
        name='logout'
    ),
    url(
        r'^password/change/$',
        password_change,
        {
            'template_name': 'authentication/auth_form.html',
            'extra_context': {
                'title': 'Changer le mot de passe',
                'action': 'Changer le mot de passe'
            }
        },
        name='password_change'
    ),
    url(r'^password/change/done/$', password_change_done, name='password_change_done'),
]
