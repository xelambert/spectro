from django.forms import ModelForm
from django import forms

class MeasurementForm(forms.Form):
    file  = forms.FileField()