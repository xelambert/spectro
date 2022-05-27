from django.forms import ModelForm
from django import forms

class MeasurementForm(forms.Form):
    #class Meta:
        #model = Student
        #fields = ['name','email','phone','course']
    file  = forms.FileField()