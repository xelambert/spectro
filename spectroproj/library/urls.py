from django.urls import path
from . import views

urlpatterns = [
    path('', views.measurements_list, name='measurements_list'),
    path('add-measurement/', views.addMeasurement, name="add-measurement"),
    path('measurement_details/', views.measurementDetails, name="measurement-details"),
]