from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time
import logging

from .services.translation_service import translation_service

logger = logging.getLogger(__name__)

def translator_ui(request):
    """Main translator interface"""
    return render(request, 'translator/index.html')

@api_view(['POST'])
def translate_text(request):
    """API endpoint for translation"""
    start_time = time.time()
    
    try:
        data = request.data
        
        text = data.get('text', '').strip()
        source_lang = data.get('source_lang', 'en').lower()
        target_lang = data.get('target_lang', 'es').lower()
        
        # Validation
        if not text:
            return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(text) > 1000:
            return Response({'error': 'Text too long. Maximum 1000 characters.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check support
        if not translation_service.get_model_name(source_lang, target_lang):
            return Response({'error': f'Translation from {source_lang} to {target_lang} not supported'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Translate
        translated_text = translation_service.translate_text(text, source_lang, target_lang)
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return Response({
            'original_text': text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'response_time_ms': response_time,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def supported_languages(request):
    """Get supported languages"""
    languages = translation_service.get_supported_languages()
    return Response({
        'languages': languages,
        'total': len(languages),
        'success': True
    })

@api_view(['GET'])
def health_check(request):
    """Health check"""
    return Response({
        'status': 'healthy',
        'service': 'AI Translator',
        'success': True
    })