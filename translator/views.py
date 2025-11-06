from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time
import logging

from .services.translation_service import translation_service

logger = logging.getLogger(__name__)

def translator_ui(request):
    """
    Render the main translator interface
    """
    return render(request, 'translator/index.html')

@api_view(['POST'])
def translate_text(request):
    """
    API endpoint for translation with comprehensive error handling
    """
    start_time = time.time()
    
    try:
        data = request.data
        
        # Extract and validate input data
        text = data.get('text', '').strip()
        source_lang = data.get('source_lang', 'en').lower()
        target_lang = data.get('target_lang', 'es').lower()
        
        # Validation checks
        if not text:
            return Response({
                'error': 'Text is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(text) > 1000:
            return Response({
                'error': 'Text too long. Maximum 1000 characters allowed.',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if source_lang == target_lang:
            return Response({
                'error': 'Source and target languages cannot be the same.',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if source language is supported
        if not translation_service.is_language_supported(source_lang):
            supported_languages = translation_service.get_supported_languages()
            return Response({
                'error': f'Source language "{source_lang}" is not supported.',
                'supported_languages': list(supported_languages.keys()),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if target language is supported
        if not translation_service.is_language_supported(target_lang):
            supported_languages = translation_service.get_supported_languages()
            return Response({
                'error': f'Target language "{target_lang}" is not supported.',
                'supported_languages': list(supported_languages.keys()),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get translation path information
        translation_info = translation_service.get_translation_info(source_lang, target_lang)
        
        # Check if translation is available for this language pair
        if not translation_info['available']:
            available_languages = list(translation_service.get_available_languages().keys())
            return Response({
                'error': f'Translation from {source_lang} to {target_lang} is not currently available.',
                'available_languages': available_languages,
                'suggestion': 'Try using English as an intermediate language.',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform the translation
        logger.info(f"Starting translation: {source_lang} -> {target_lang}")
        translated_text = translation_service.translate_text(
            text, source_lang, target_lang
        )
        
        # Calculate response time
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # Log successful translation
        logger.info(f"Translation completed: {source_lang}->{target_lang} in {response_time}ms")
        
        # Return successful response
        return Response({
            'original_text': text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'translation_type': translation_info['type'],
            'translation_path': translation_info['path'],
            'translation_description': translation_info['description'],
            'response_time_ms': response_time,
            'success': True
        })
        
    except Exception as e:
        # Log the error with detailed context
        logger.error(f"Translation error: {str(e)}", exc_info=True)
        
        # Return user-friendly error message
        error_message = str(e)
        if 'model' in error_message.lower() and 'not found' in error_message.lower():
            error_message = 'Translation service temporarily unavailable. Please try again in a moment.'
        elif 'failed to load' in error_message.lower():
            error_message = 'Translation model is currently loading. Please try again shortly.'
        
        return Response({
            'error': error_message,
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def supported_languages(request):
    """
    Get comprehensive information about supported languages
    """
    try:
        all_languages = translation_service.get_supported_languages()
        available_languages = translation_service.get_available_languages()
        african_languages = translation_service.get_african_languages()
        
        # Calculate statistics
        total_languages = len(all_languages)
        total_available = len(available_languages)
        total_african = len(african_languages)
        
        # Identify unavailable languages
        unavailable_languages = {
            code: name for code, name in all_languages.items() 
            if code not in available_languages
        }
        
        return Response({
            'languages': {
                'all': all_languages,
                'available': available_languages,
                'unavailable': unavailable_languages,
                'african': african_languages
            },
            'statistics': {
                'total_languages': total_languages,
                'total_available': total_available,
                'total_unavailable': len(unavailable_languages),
                'total_african': total_african,
                'coverage_percentage': round((total_available / total_languages) * 100, 1)
            },
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        return Response({
            'error': 'Failed to retrieve language information',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def health_check(request):
    """
    Comprehensive health check endpoint
    """
    try:
        # Basic service health
        supported_languages_count = len(translation_service.get_supported_languages())
        available_languages_count = len(translation_service.get_available_languages())
        loaded_models_count = len(translation_service.models)
        
        health_status = {
            'status': 'healthy',
            'service': 'AI Translator API',
            'timestamp': time.time(),
            'version': '1.0.0',
            'metrics': {
                'supported_languages': supported_languages_count,
                'available_languages': available_languages_count,
                'loaded_models': loaded_models_count,
                'model_loading_enabled': translation_service._initialized
            },
            'success': True
        }
        
        # Add warning if many models aren't available
        if available_languages_count < supported_languages_count:
            health_status['warning'] = f'{supported_languages_count - available_languages_count} languages require pivot translation'
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'success': False
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
def translation_info(request):
    """
    Get detailed translation path information for a language pair
    """
    try:
        source_lang = request.GET.get('source_lang', 'en').lower()
        target_lang = request.GET.get('target_lang', 'es').lower()
        
        # Validate input parameters
        if not source_lang or not target_lang:
            return Response({
                'error': 'Both source_lang and target_lang parameters are required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if languages are supported
        if not translation_service.is_language_supported(source_lang):
            return Response({
                'error': f'Source language "{source_lang}" is not supported',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not translation_service.is_language_supported(target_lang):
            return Response({
                'error': f'Target language "{target_lang}" is not supported',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get translation information
        translation_info = translation_service.get_translation_info(source_lang, target_lang)
        
        # Add additional context
        response_data = {
            'source_lang': source_lang,
            'target_lang': target_lang,
            'translation_info': translation_info,
            'language_names': {
                'source': translation_service.supported_languages.get(source_lang, 'Unknown'),
                'target': translation_service.supported_languages.get(target_lang, 'Unknown')
            },
            'success': True
        }
        
        # Add suggestions for unavailable translations
        if not translation_info['available']:
            response_data['suggestions'] = [
                f'Try translating from {source_lang} to English first, then from English to {target_lang}',
                'Check back later as we are constantly adding new language support'
            ]
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Translation info error: {str(e)}")
        return Response({
            'error': 'Failed to get translation information',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def language_details(request, lang_code):
    """
    Get detailed information about a specific language
    """
    try:
        lang_code = lang_code.lower()
        
        # Check if language is supported
        if not translation_service.is_language_supported(lang_code):
            return Response({
                'error': f'Language "{lang_code}" is not supported',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get basic language info
        language_name = translation_service.supported_languages.get(lang_code)
        is_available = lang_code in translation_service.get_available_languages()
        is_african = lang_code in translation_service.get_african_languages()
        
        # Find available translation pairs for this language
        available_translations = []
        for (source, target), model_name in translation_service.model_mapping.items():
            if source == lang_code:
                available_translations.append({
                    'target': target,
                    'target_name': translation_service.supported_languages.get(target),
                    'type': 'direct'
                })
            elif target == lang_code:
                available_translations.append({
                    'source': source,
                    'source_name': translation_service.supported_languages.get(source),
                    'type': 'direct'
                })
        
        # Response data
        response_data = {
            'code': lang_code,
            'name': language_name,
            'availability': {
                'is_available': is_available,
                'can_translate_from': is_available,
                'can_translate_to': is_available
            },
            'category': 'african' if is_african else 'international',
            'available_translations': available_translations,
            'total_direct_pairs': len([t for t in available_translations if t['type'] == 'direct']),
            'success': True
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Language details error for {lang_code}: {str(e)}")
        return Response({
            'error': 'Failed to get language details',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def system_status(request):
    """
    Get comprehensive system status and metrics
    """
    try:
        # Basic system information
        import torch
        import platform
        import psutil
        
        system_info = {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'django_version': '4.2.7',
            'torch_version': torch.__version__,
            'device': str(translation_service.device) if translation_service._initialized else 'Not initialized',
            'cuda_available': torch.cuda.is_available(),
        }
        
        # Memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        system_info['memory_usage'] = {
            'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
            'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
            'percent': process.memory_percent()
        }
        
        # Translation service status
        translation_status = {
            'initialized': translation_service._initialized,
            'loaded_models': len(translation_service.models),
            'supported_languages': len(translation_service.supported_languages),
            'available_languages': len(translation_service.get_available_languages()),
            'model_mappings': len(translation_service.model_mapping)
        }
        
        return Response({
            'system': system_info,
            'translation_service': translation_status,
            'timestamp': time.time(),
            'success': True
        })
        
    except Exception as e:
        logger.error(f"System status error: {str(e)}")
        return Response({
            'error': 'Failed to get system status',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def batch_translate(request):
    """
    Translate multiple texts in a single request
    """
    start_time = time.time()
    
    try:
        data = request.data
        texts = data.get('texts', [])
        source_lang = data.get('source_lang', 'en').lower()
        target_lang = data.get('target_lang', 'es').lower()
        
        # Validation
        if not texts:
            return Response({
                'error': 'Texts array is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(texts) > 10:
            return Response({
                'error': 'Maximum 10 texts allowed per batch',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate each text
        for i, text in enumerate(texts):
            if len(text) > 500:
                return Response({
                    'error': f'Text {i+1} too long. Maximum 500 characters per text.',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check translation availability
        translation_info = translation_service.get_translation_info(source_lang, target_lang)
        if not translation_info['available']:
            return Response({
                'error': f'Translation from {source_lang} to {target_lang} is not available',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform batch translation
        translations = []
        for text in texts:
            try:
                translated_text = translation_service.translate_text(text, source_lang, target_lang)
                translations.append({
                    'original': text,
                    'translated': translated_text,
                    'success': True
                })
            except Exception as e:
                translations.append({
                    'original': text,
                    'error': str(e),
                    'success': False
                })
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # Calculate success rate
        successful_translations = [t for t in translations if t['success']]
        success_rate = len(successful_translations) / len(translations) * 100
        
        return Response({
            'translations': translations,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'translation_info': translation_info,
            'batch_metrics': {
                'total_texts': len(texts),
                'successful': len(successful_translations),
                'failed': len(translations) - len(successful_translations),
                'success_rate': round(success_rate, 1),
                'response_time_ms': response_time
            },
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Batch translation error: {str(e)}")
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)