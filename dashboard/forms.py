from django import forms


class QuestionForm(forms.Form):
    question = forms.CharField(widget=forms.Textarea)
