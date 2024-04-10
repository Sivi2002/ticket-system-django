# forms.py
from django import forms

from .models import Ticket

class AppForm(forms.Form):
    CHOICES = (
        ('', 'Select ticket type'),
        ('Access Request', 'Access Request'),
        ('Query', 'Query'),
        ('Defect', 'Defect'),
        ('Enhancement', 'Enhancement')
    )

    subject = forms.CharField(max_length=255,widget=forms.TextInput(attrs={'placeholder': 'Enter your subject'}))
    discription = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={'placeholder': 'Enter your discription', 'cols': 10, 'rows': 5}))
    ticket_type = forms.ChoiceField(choices=CHOICES, required=True, initial=None)
    comment = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Enter your comment'}))
    active = forms.BooleanField()
    file = forms.FileField()
    
    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If instance is provided, populate form fields with instance data
        if instance:
            self.fields['subject'].initial = instance.subject
            self.fields['discription'].initial = instance.discription
            self.fields['ticket_type'].initial = instance.ticket_type
            self.fields['comment'].initial = instance.comment
            self.fields['active'].initial = instance.active
            self.fields['file'].initial = instance.file
    
    
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    