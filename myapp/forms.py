from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Endpoint

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class EndpointForm(forms.ModelForm):
    class Meta:
        model = Endpoint
        fields = ['url']

class CustomJSForm(forms.Form):
    endpoint = forms.ModelChoiceField(queryset=Endpoint.objects.all(), label="Select Endpoint")
    custom_js = forms.CharField(widget=forms.Textarea, label="Custom JS")

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']