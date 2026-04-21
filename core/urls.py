from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('monitoring-bendahara/', views.monitoring_bendahara, name='monitoring_bendahara'),
]
