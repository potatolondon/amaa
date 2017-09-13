# Put public views here
from django.shortcuts import render


def home(request):
    return render(request, template_name='amaa/home.html', context={})
