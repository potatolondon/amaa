from django.shortcuts import render


def home(request):
    return render(request, template_name='dashboard/home.html', context={})


def big_screen(request):
    return render(request, template_name='dashboard/big_screen.html', context={})


def all_questions(request):
    return render(request, template_name='dashboard/all_questions.html', context={})
