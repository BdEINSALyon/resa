import json

from django import forms
import requests
from account.models import OAuthService
from permissions.models import AzureGroup


class AzureGroupForm(forms.ModelForm):
    class Meta:
        model = AzureGroup
        fields = ('group', 'azure_id', 'azure_name')

    azure_id = forms.ChoiceField(choices=(('', 'Please enable Office 365 for this app'),))
    azure_name = forms.CharField(widget=forms.HiddenInput(), required=False)

    @staticmethod
    def get_groups():
        service = OAuthService.objects.filter(name='microsoft').first()
        if service is None:
            return ('', 'Please enable Office 365 for this app'),
        data = requests.get(
            service.provider.graph('/groups?$orderby=displayName'),
            headers={
                'Authorization': 'Bearer {}'.format(service.provider.retrieve_app_token()['access_token'])
            }).json()

        if data.get('error'):
            return ('', 'Error while fetching groups : {}'.format(data.get('error').get('message'))),

        groups = data.get('value', [])
        form_data = []
        for group in groups:
            id_name = '{}_{}'.format(group['id'], group['displayName'])
            form_data.append((id_name, group['displayName']))
        return form_data

    def __init__(self, *args, **kwargs):
        # receive a tuple/list for custom choices
        super(AzureGroupForm, self).__init__(*args, **kwargs)
        self.fields['azure_id'].choices = AzureGroupForm.get_groups()
        self.initial['azure_id'] = "{}_{}".format(self.instance.azure_id, self.instance.azure_name)

    def clean(self):
        super().clean()
        data = self.cleaned_data.get('azure_id').split('_', maxsplit=1)
        self.cleaned_data['azure_id'] = data[0]
        self.cleaned_data['azure_name'] = data[1]
