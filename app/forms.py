from django import forms
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
REQUIRED_CATEGORY_FIELDS = (
    'destinations',
    'accommodations',
    'family_members',
)
CATEGORY_HELPER_TEXT = (
    'For destinations, accommodations, and family members, check at least one option. '
    'Activities are always optional. When Always is checked, only family members can be specified.'
)


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
            'weather_hot',
            'weather_cold',
            'destinations',
            'activities',
            'accommodations',
            'family_members',
        ]
        widgets = {
            'name': TEXT_INPUT,
            'section': SELECT,
            'notes': TEXTAREA,
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
        if cleaned_data.get('always'):
            return cleaned_data

        has_required_category = any(
            cleaned_data.get(field_name) for field_name in REQUIRED_CATEGORY_FIELDS
        )
        if not has_required_category:
            raise ValidationError(CATEGORY_HELPER_TEXT)

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
