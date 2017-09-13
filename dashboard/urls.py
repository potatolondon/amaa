from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^big-screen/$', views.big_screen, name='big_screen'),
    url(r'^all-questions/$', views.all_questions, name='all_questions'),
    url(r'^$', views.home, name='home'),
]
