from django import forms
from .models import Community

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'rules', 'tags']

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags and tags.count() > 3:
            raise forms.ValidationError(
                "You can select a maximum of 3 tags."
            )
        return tags
