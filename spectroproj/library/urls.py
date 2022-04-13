from django.urls import path
from . import views

urlpatterns = [
    path('', views.measurements_list, name='measurements_list'),
]