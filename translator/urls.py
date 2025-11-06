from django.urls import path
from . import views

urlpatterns = [
    path('', views.translator_ui, name='translator_ui'),
    path('api/translate/', views.translate_text, name='translate'),
    path('api/languages/', views.supported_languages, name='supported_languages'),
    path('api/health/', views.health_check, name='health_check'),
]