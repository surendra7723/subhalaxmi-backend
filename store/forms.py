from django_json_widget.widgets import JSONEditorWidget
from django import forms
from .models import Product, ContactMessage
from .constants import AVAILABLE_SIZES, COLOR_CHOICES, SEASON_CHOICES

class ProductAdminForm(forms.ModelForm):
    available_sizes=forms.MultipleChoiceField(
        choices=AVAILABLE_SIZES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    available_colors=forms.MultipleChoiceField(
        choices=COLOR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    season = forms.CharField(
        max_length=50,
        widget=forms.Select(choices=SEASON_CHOICES),
        required=False,
    )
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'available_sizes': JSONEditorWidget(),
            'available_colors': JSONEditorWidget(),
        }

    def clean_available_sizes(self):
        """Validate the JSON input for available_sizes."""
        data = self.cleaned_data['available_sizes']
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)  # Parse the JSON string
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format.")
        return data


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'phone', 'subject', 'message', 'newsletter_signup']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (234) 567-8900'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Tell us how we can help you...'
            }),
            'newsletter_signup': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone': 'Phone Number (Optional)',
            'subject': 'Subject',
            'message': 'Message',
            'newsletter_signup': "I'd like to receive updates about new collections and special offers"
        }
