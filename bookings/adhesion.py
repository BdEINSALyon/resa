import requests
from django.conf import settings


class AdhesionAPI:
    app_id = settings.ADHESION_APP_ID
    app_secret = settings.ADHESION_APP_SECRET
    token = None

    @classmethod
    def refresh_token(cls):
        if cls.token is None:
            token_request = requests.get('https://adhesion.bde-insa-lyon.fr/api/auth',
                                         params={'app_id': cls.app_id, 'app_secret': cls.app_secret})
            cls.token = token_request.json()['token']

    @classmethod
    def get_va(cls, card_id):
        cls.refresh_token()
        return requests.get(
            'https://adhesion.bde-insa-lyon.fr/api/membership',
            {
                'code': card_id
            }, headers={
                'Authorization': 'Bearer {}'.format(cls.token)
            }
        ).json()
