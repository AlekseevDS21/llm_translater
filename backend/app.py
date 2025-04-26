from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
import traceback
import requests
import json
import re
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Configure logging with more details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check if API key is available and log warning if not
if not os.getenv("OPENROUTER_API_KEY"):
    logger.warning("OPENROUTER_API_KEY not found in environment variables")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Модели для использования с запасными вариантами
LLM_MODELS = [
    "deepseek/deepseek-chat:free",
    "mistralai/mistral-large-latest:free",
    "anthropic/claude-3-haiku-20240307:free",
    "meta-llama/llama-3-8b-instruct:free",
    "gryphe/mythomist-7b:free"
]

class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

def is_valid_translation(source_text, translated_text, source_language, target_language):
    """
    Проверяет, является ли перевод валидным:
    - Не совпадает с исходным текстом
    - Не содержит пояснений и комментариев переводчика
    - Не пустой
    """
    # Удаляем лишние пробелы для сравнения
    source_clean = re.sub(r'\s+', ' ', source_text.strip()).lower()
    translated_clean = re.sub(r'\s+', ' ', translated_text.strip()).lower()
    
    # Проверка на идентичность текстов
    if source_clean == translated_clean:
        logger.warning(f"Translation output matches input exactly")
        return False
    
    # Проверка на пустой результат
    if not translated_clean:
        logger.warning("Translation is empty")
        return False
    
    # Проверка на наличие слов, указывающих на метакомментарии переводчика
    meta_patterns = [
        r'translation[:\s]',
        r'translated[:\s]',
        r'here is[:\s]',
        r'перевод[:\s]',
        r'\[.*?\]',  # Текст в квадратных скобках
        r'\(.*?\)'   # Текст в круглых скобках
    ]
    
    for pattern in meta_patterns:
        if re.search(pattern, translated_clean, re.IGNORECASE):
            logger.warning(f"Translation contains meta commentary matching pattern: {pattern}")
            return False
    
    # Дополнительные проверки - используем эвристику "количество символов"
    # Если языки используют разные алфавиты и перевод содержит оригинальные символы, это может быть проблемой
    
    # Если исходный язык использует кириллицу, а целевой латиницу (или наоборот)
    cyrillic = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    latin = 'abcdefghijklmnopqrstuvwxyz'
    
    if source_language.lower() in ['russian', 'ukrainian', 'bulgarian', 'serbian'] and \
       target_language.lower() in ['english', 'spanish', 'french', 'german', 'italian']:
        # Проверяем, что в переводе мало кириллических символов
        cyrillic_count = sum(1 for c in translated_clean if c.lower() in cyrillic)
        if cyrillic_count > len(translated_clean) * 0.3:  # Если более 30% символов кириллические
            logger.warning(f"Translation to {target_language} contains too many Cyrillic characters")
            return False
            
    elif source_language.lower() in ['english', 'spanish', 'french', 'german', 'italian'] and \
         target_language.lower() in ['russian', 'ukrainian', 'bulgarian', 'serbian']:
        # Проверяем, что в переводе мало латинских символов
        latin_count = sum(1 for c in translated_clean if c.lower() in latin)
        if latin_count > len(translated_clean) * 0.3:  # Если более 30% символов латинские
            logger.warning(f"Translation to {target_language} contains too many Latin characters")
            return False
            
    return True

async def perform_translation(text, source_lang, target_lang, model, api_key, site_url, site_name):
    """
    Выполняет перевод с помощью указанной модели
    """
    # Улучшенный промпт со строгими ограничениями на вывод модели
    prompt = f"""INSTRUCTION: Translate the following text from {source_lang} to {target_lang}. 

EXTREMELY IMPORTANT: You MUST return ONLY the translated text without ANY additional text. 
- NO comments
- NO notes
- NO explanations
- NO introductions
- NO formatting marks
- NO "here's the translation"
- NOTHING except the plain translated text

TEXT TO TRANSLATE:
{text}"""

    try:
        # Используем библиотеку OpenAI
        logger.debug(f"Using OpenAI client with model: {model}")
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": site_url,
                    "X-Title": site_name,
                },
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Получаем текст из ответа
            translated_text = completion.choices[0].message.content
            logger.info(f"Translation successful with OpenAI client")
            
            # Проверяем валидность перевода
            if is_valid_translation(text, translated_text, source_lang, target_lang):
                return translated_text, model, None
            else:
                return None, model, "Invalid translation: output too similar to input"
            
        except Exception as openai_error:
            # Если получили ошибку с OpenAI клиентом, логируем и пробуем через requests
            logger.warning(f"OpenAI client error: {str(openai_error)}. Trying with requests...")
            
            # Если клиент OpenAI не работает, используем requests напрямую
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": site_url,
                    "X-Title": site_name,
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"API response data: {response_data}")
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    if 'message' in response_data['choices'][0] and 'content' in response_data['choices'][0]['message']:
                        translated_text = response_data['choices'][0]['message']['content']
                        logger.info("Translation successful with requests")
                        
                        # Проверяем валидность перевода
                        if is_valid_translation(text, translated_text, source_lang, target_lang):
                            return translated_text, model, None
                        else:
                            return None, model, "Invalid translation: output too similar to input"
                
                # Если не удалось найти текст перевода в ответе
                error_msg = f"Unexpected response structure: {response_data}"
                logger.error(error_msg)
                return None, model, error_msg
            else:
                error_msg = f"OpenRouter API returned status code {response.status_code}: {response.text}"
                logger.error(error_msg)
                return None, model, error_msg
            
    except Exception as e:
        error_msg = f"Error during translation: {str(e)}"
        logger.error(error_msg)
        return None, model, error_msg

@app.post("/translate")
async def translate_text(request: TranslationRequest):
    try:
        # Log translation request
        logger.info(f"Translation request: {request.source_language} to {request.target_language}")
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("API key not found")
            raise HTTPException(status_code=500, detail="API key not configured")
        
        site_url = os.getenv("SITE_URL", "http://llm-translator.example.com")
        site_name = os.getenv("SITE_NAME", "LLM Translator")
        
        logger.info(f"Using site URL: {site_url}, site name: {site_name}")
        
        # Попытка перевести текст, используя разные модели, если требуется
        errors = []
        
        # Если языки совпадают, не выполняем перевод
        if request.source_language.lower() == request.target_language.lower():
            return {"translated_text": request.text, "model_used": "none (same language)"}
        
        for model in LLM_MODELS:
            translated_text, used_model, error = await perform_translation(
                request.text, 
                request.source_language, 
                request.target_language,
                model, 
                api_key, 
                site_url, 
                site_name
            )
            
            if translated_text:
                # Успешный перевод
                return {"translated_text": translated_text, "model_used": used_model}
            
            # Сохраняем ошибку для логирования
            errors.append(f"Model {model}: {error}")
            logger.warning(f"Translation with {model} failed: {error}. Trying next model.")
        
        # Если все модели не смогли выполнить правильный перевод
        all_errors = "\n".join(errors)
        logger.error(f"All translation attempts failed:\n{all_errors}")
        raise HTTPException(status_code=500, detail="Failed to get valid translation from any model")
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log unexpected errors with traceback for отладка
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected error in translation: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/health")
async def health_check():
    # Check if API key is available
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"status": "warning", "message": "API key not configured"}
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)