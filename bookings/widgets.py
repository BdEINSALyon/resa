from django import forms
from django.db.models import QuerySet
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class ResourcesWidget(forms.widgets.Widget):
    def value_from_datadict(self, data, files, name):
        counts = {}
        for key, value in data.items():
            if key.startswith(name):
                if value == 'on':
                    value = 1
                elif value == '' or int(value) == 0:
                    continue
                counts[key.split('_')[1]] = int(value)

        return counts

    def render(self, name, value, attrs=None):
        if value is None:
            value = {}
        elif isinstance(value, list) and len(value) > 0:
            # We're creating a new booking
            if not isinstance(value[0], dict):
                value = {resource: 1 if resource.is_countable() else True for resource in value if resource is not None}

        elif isinstance(value, QuerySet) and len(value) > 0:
            if not isinstance(value[0], dict):
                value = {resource: resource.bookings.get(occurrence=self.occurrence).count if resource.is_countable() else True for resource in value if resource is not None}

        output = [
            format_html('<div id="resources">'),
            format_html("""
              <input id="search" class="search form-control" placeholder="Rechercher" />
            """),
            format_html('<div class="limit-height">'),
            format_html('<table class="table table-hover">'),
            format_html('<tbody class="list">'),
        ]

        choices = self.render_choices(value)
        if choices:
            output.append(choices)

        output.append(format_html('</tbody></table></div></div>'))

        return mark_safe('\n'.join(output))

    def render_choices(self, selected_choices):
        output = []
        for resource in self.choices:
            output.append(self.render_choice(selected_choices, resource))
        return '\n'.join(output)

    def render_choice(self, selected_choices, resource):
        if resource is None:
            return ''

        choices = {}

        if isinstance(selected_choices, dict):
            for k, v in selected_choices.items():
                if not isinstance(k, str):
                    k = str(k.pk)
                choices[k] = v

        elif isinstance(selected_choices, QuerySet):
            for choice in selected_choices:
                choices[str(choice.pk)] = 1

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

        res_id = str(pk)
        if res_id in choices:
            value = choices.get(res_id)
            if not resource.is_countable():
                value = values.get(value)

        res_id = 'resources_' + res_id

        choice_html = format_html(
            '<tr>'
            '<td class="name"><label for="{id}">{name}',
            name=name, id=res_id
        )
        if resource.is_countable():
            choice_html += format_html(' (max {count})', count=resource.number)

        choice_html += format_html(
            '</label></td>'
            '<td class="category">{category}</td>'
            '<td>{field}</td>'
            '</tr>',
            category=category, field=field.render('resources_' + str(pk), value)
        )

        return choice_html
