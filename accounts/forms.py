from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "age",
            "phone",
            "address",
            "bio",
            "profile_pic",
            "favourite_tags",
        ]
        widgets = {
            "favourite_tags": forms.CheckboxSelectMultiple,
        }

    def clean_favourite_tags(self):
        tags = self.cleaned_data.get("favourite_tags")
        if tags and tags.count() > 5:
            raise forms.ValidationError(
                "You can select up to 5 favourite interests only."
            )
        return tags
