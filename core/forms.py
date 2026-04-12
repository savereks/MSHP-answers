from core.models import Question, Answer
from django import forms

class AnswerForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)
