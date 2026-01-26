#!/usr/bin/env python3
"""
Простой тест подключения к LiteLLM через proxy.merkulov.ai
"""
import os
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from litellm import completion

# Загружаем .env
load_dotenv()

def test_litellm():
    """Тестирует подключение к LiteLLM."""
    print("🧪 Тестирование LiteLLM подключения...")
    print(f"Model: {os.getenv('LLM_MODEL', 'gpt-4')}")
    print(f"API Base: {os.getenv('LLM_API_BASE', 'Not set')}")
    print(f"API Key: {os.getenv('LLM_API_KEY', 'Not set')[:10]}...")
    print()
    
    try:
        response = completion(
            model=os.getenv("LLM_MODEL", "gpt-4"),
            messages=[{"role": "user", "content": "Say 'Hello from LiteLLM!' in one sentence."}],
            api_key=os.getenv("LLM_API_KEY"),
            api_base=os.getenv("LLM_API_BASE"),
            timeout=30.0,
        )
        
        content = response.choices[0].message.content
        print("✅ Успешно!")
        print(f"Ответ: {content}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\nПроверьте:")
        print("1. .env файл существует и содержит правильные значения")
        print("2. Интернет соединение работает")
        print("3. API ключ действителен")
        return False

if __name__ == "__main__":
    success = test_litellm()
    sys.exit(0 if success else 1)
