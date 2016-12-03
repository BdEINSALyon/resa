from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class ResourcesWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        print(value)
        if value is None:
            value = {}
        if isinstance(value, list):
            value = {resource: 1 if resource.is_countable() else True for resource in value if resource is not None}

        output = [format_html('<table class="table table-hover">'),
                  format_html('<tr><th>Ressource</th><th>Catégorie</th><th>Sélectionné</th></tr>')]

        choices = self.render_choices(value)
        if choices:
            output.append(choices)

        output.append('</table>')

        return mark_safe('\n'.join(output))

    def render_choices(self, selected_choices):
        output = []
        for resource in self.choices:
            output.append(self.render_choice(selected_choices, resource))
        return '\n'.join(output)

    def render_choice(self, selected_choices, resource):
        if resource is None:
            return ''

        name = resource.name
        category = resource.category.name
        pk = resource.pk
        if resource.is_countable():
            field = forms.NumberInput(attrs={'class': 'form-control'})
            value = 0
        else:
            field = forms.CheckboxInput()
            value = False

        values = {0: False, 1: True}

        if resource in selected_choices:
            value = selected_choices.get(resource)
            if not resource.is_countable():
                value = values.get(value)

        return format_html('<tr>'
                           '<td>{name}</td>'
                           '<td>{category}</td>'
                           '<td>{field}</td>'
                           '</tr>', name=name, category=category, field=field.render(pk, value))
