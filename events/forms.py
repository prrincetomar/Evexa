from django import forms
from .models import Event, Tag


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'interest',
            'description',
            'location',
            'date',
            'start_time',
            'end_time',
            'max_participants',
            'tags',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags and tags.count() > 5:
            raise forms.ValidationError("You can select at most 5 tags.")
        return tags
