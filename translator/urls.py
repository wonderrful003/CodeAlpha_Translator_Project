from django.urls import path
from . import views

urlpatterns = [
    # UI Routes
    path('', views.translator_ui, name='translator_ui'),
    
    # API Routes
    path('api/translate/', views.translate_text, name='translate'),
    path('api/batch-translate/', views.batch_translate, name='batch_translate'),
    path('api/languages/', views.supported_languages, name='supported_languages'),
    path('api/languages/<str:lang_code>/', views.language_details, name='language_details'),
    path('api/translation-info/', views.translation_info, name='translation_info'),
    path('api/health/', views.health_check, name='health_check'),
    path('api/status/', views.system_status, name='system_status'),
]