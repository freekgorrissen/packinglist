from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

from app.models import (
    AccommodationType,
    Activity,
    DestinationCategory,
    FamilyMember,
    MemberType,
    PackingAllocation,
    PackingItem,
    PackingSection,
    Trip,
)

TEXT_INPUT = forms.TextInput(attrs={'class': 'form-control'})
TEXTAREA = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
SINGLE_LINE_TEXT = forms.TextInput(attrs={'class': 'form-control'})
NUMBER_INPUT = forms.NumberInput(attrs={'class': 'form-control'})
SELECT = forms.Select(attrs={'class': 'form-select'})
RADIO = forms.RadioSelect()

PACKING_ITEM_TRIP_CATEGORY_FIELDS = (
    'destinations',
    'activities',
    'accommodations',
)
PACKING_ITEM_ALWAYS_GREYED_FIELDS = (
    'weather_hot',
    'weather_cold',
    *PACKING_ITEM_TRIP_CATEGORY_FIELDS,
)
PACKING_ITEM_CATEGORY_FIELDS = PACKING_ITEM_TRIP_CATEGORY_FIELDS + ('family_members',)

FAMILY_MEMBERS_REQUIRED_TEXT = 'Select at least one family member.'


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ['name', 'member_type', 'icon', 'notes']
        widgets = {
            'name': TEXT_INPUT,
            'member_type': RADIO,
            'icon': RADIO,
            'notes': TEXTAREA,
        }


class DestinationCategoryForm(forms.ModelForm):
    class Meta:
        model = DestinationCategory
        fields = ['name']
        widgets = {'name': TEXT_INPUT}


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name']
        widgets = {'name': TEXT_INPUT}


class AccommodationTypeForm(forms.ModelForm):
    class Meta:
        model = AccommodationType
        fields = ['name']
        widgets = {'name': TEXT_INPUT}


class PackingSectionForm(forms.ModelForm):
    class Meta:
        model = PackingSection
        fields = ['name', 'sort_order']
        widgets = {
            'name': TEXT_INPUT,
            'sort_order': NUMBER_INPUT,
        }


class PackingItemForm(forms.ModelForm):
    class Meta:
        model = PackingItem
        fields = [
            'name',
            'section',
            'notes',
            'always',
            'packing_allocation',
            'family_members',
            'accommodations',
            'destinations',
            'activities',
            'weather_hot',
            'weather_cold',
        ]
        widgets = {
            'name': TEXT_INPUT,
            'section': SELECT,
            'notes': SINGLE_LINE_TEXT,
            'always': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'packing_allocation': RADIO,
            'weather_hot': forms.CheckboxInput(),
            'weather_cold': forms.CheckboxInput(),
            'destinations': forms.CheckboxSelectMultiple,
            'activities': forms.CheckboxSelectMultiple,
            'accommodations': forms.CheckboxSelectMultiple,
            'family_members': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_add = self.data.get('batch_add') in ('on', '1') if self.data else False
        if self.batch_add:
            self.fields['name'].required = False
        self.fields['always'].help_text = (
            'Include this item on every trip. You can still limit it to specific family members.'
        )
        self.fields['packing_allocation'].label = 'Who packs this item?'
        self.fields['packing_allocation'].help_text = (
            'Individual: one line per person. Adults / children: one shared line per group. '
            'Shared: one line for everyone on the trip.'
        )
        self.fields['weather_hot'].label = 'Hot'
        self.fields['weather_cold'].label = 'Cold'
        self._set_trip_category_fields_disabled(self._is_always_checked())

    def _batch_names(self):
        if not self.data:
            return []
        return [name.strip() for name in self.data.getlist('batch_names') if name.strip()]

    def _is_always_checked(self):
        if 'always' in self.data:
            return self.data.get('always') in ('on', 'true', 'True', '1')
        if self.instance.pk:
            return self.instance.always
        return False

    def _set_trip_category_fields_disabled(self, disabled):
        for field_name in PACKING_ITEM_ALWAYS_GREYED_FIELDS:
            self.fields[field_name].disabled = disabled

    def clean(self):
        cleaned_data = super().clean()
        if self.batch_add:
            batch_names = self._batch_names()
            if not batch_names:
                raise ValidationError('Enter at least one item name for batch add.')
            self.batch_names = batch_names
            cleaned_data['name'] = batch_names[0]
        elif not cleaned_data.get('name'):
            self.add_error('name', 'This field is required.')

        if not cleaned_data.get('family_members'):
            raise ValidationError(FAMILY_MEMBERS_REQUIRED_TEXT)

        if cleaned_data.get('always'):
            return cleaned_data
        
        if not any(cleaned_data.get(field_name) for field_name in PACKING_ITEM_TRIP_CATEGORY_FIELDS):
            raise ValidationError('Select at least one destination, activity, or accommodation.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if instance.always:
            instance.destinations.clear()
            instance.activities.clear()
            instance.accommodations.clear()
            instance.weather_hot = False
            instance.weather_cold = False
            if commit:
                instance.save(update_fields=['weather_hot', 'weather_cold'])
        return instance

    def save_new_item(self, name):
        item = PackingItem(
            name=name,
            section=self.cleaned_data['section'],
            notes=self.cleaned_data.get('notes', ''),
            always=self.cleaned_data.get('always', False),
            packing_allocation=self.cleaned_data['packing_allocation'],
        )
        if item.always:
            item.weather_hot = False
            item.weather_cold = False
        else:
            item.weather_hot = self.cleaned_data.get('weather_hot', False)
            item.weather_cold = self.cleaned_data.get('weather_cold', False)
        item.save()
        if item.always:
            item.destinations.clear()
            item.activities.clear()
            item.accommodations.clear()
            item.family_members.set(self.cleaned_data.get('family_members', []))
        else:
            item.destinations.set(self.cleaned_data.get('destinations', []))
            item.activities.set(self.cleaned_data.get('activities', []))
            item.accommodations.set(self.cleaned_data.get('accommodations', []))
            item.family_members.set(self.cleaned_data.get('family_members', []))
        return item


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'name',
            'start_date',
            'end_date',
            'family_members',
            'destinations',
            'activities',
            'accommodations',
            'weather_hot',
            'weather_cold',
        ]
        widgets = {
            'name': TEXT_INPUT,
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'family_members': forms.CheckboxSelectMultiple,
            'destinations': forms.CheckboxSelectMultiple,
            'activities': forms.CheckboxSelectMultiple,
            'accommodations': forms.CheckboxSelectMultiple,
            'weather_hot': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weather_cold': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['weather_hot'].label = 'Hot'
        self.fields['weather_cold'].label = 'Cold'


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
