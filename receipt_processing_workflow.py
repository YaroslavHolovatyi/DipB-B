"""
Receipt Processing Workflow / Послідовність обробки чека
Complete implementation of receipt OCR processing pipeline
"""

import base64
import json
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from receipt_ocr_schema import (
    ReceiptOCRResult,
    ReceiptProcessingRequest,
    ReceiptProcessingResponse
)

# Setup logging / Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# WORKFLOW DIAGRAM / ДІАГРАМА ПОСЛІДОВНОСТІ
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                    ПОСЛІДОВНІСТЬ ОБРОБКИ ЧЕКА                           │
│                   Receipt Processing Sequence                           │
└─────────────────────────────────────────────────────────────────────────┘

1. ПРИЕМ ЗАПРОСА / REQUEST INTAKE
   ↓
   └─→ Валідація параметрів (image_path, user_id)
   └─→ Verify request parameters

2. ЗАВАНТАЖЕННЯ ЗОБРАЖЕННЯ / IMAGE LOADING
   ↓
   └─→ Прочитати файл / Read file
   └─→ Перевірити формат / Verify format (JPEG, PNG, etc.)
   └─→ Кодування в base64 / Encode to base64

3. ВИКЛИК OCR (OpenAI Vision) / OCR CALL
   ↓
   └─→ Надіслати зображення до OpenAI / Send to OpenAI
   └─→ Промпт: "Extract receipt data..." / Prompt extraction
   └─→ Отримати JSON відповідь / Get JSON response

4. ПАРСИНГ РЕЗУЛЬТАТУ / RESULT PARSING
   ↓
   └─→ Розпарсити JSON / Parse JSON
   └─→ Перевірити наявність необхідних полів / Validate required fields
   └─→ Перетворити типи даних / Convert data types

5. ВАЛІДАЦІЯ / VALIDATION
   ↓
   └─→ Pydantic валідація моделі / Pydantic model validation
   └─→ Перевірити суми (товари = сума) / Verify totals
   └─→ Перевірити дати / Validate dates
   └─→ Обробка помилок валідації / Handle validation errors

6. ЗБЕРЕЖЕННЯ / STORAGE
   ↓
   └─→ Зберегти в БД / Save to database
   └─→ Зберегти оригінальне зображення / Save original image
   └─→ Логувати результати / Log results

7. ПОВЕРНЕННЯ РЕЗУЛЬТАТУ / RETURN RESULT
   ↓
   └─→ Повернути ReceiptProcessingResponse / Return response
   └─→ Включити час обробки / Include processing time
   └─→ Статус успіху / Success status

"""


# ============================================================================
# RECEIPT PROCESSING SERVICE / СЕРВІС ОБРОБКИ ЧЕКА
# ============================================================================

class ReceiptProcessingService:
    """Service for processing receipts via OpenAI Vision API"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize service with OpenAI client"""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-vision-preview"

    async def process_receipt(
        self,
        request: ReceiptProcessingRequest
    ) -> ReceiptProcessingResponse:
        """
        Main processing method / Основний метод обробки

        Args:
            request: Processing request with image path / Запит з шляхом до зображення

        Returns:
            ReceiptProcessingResponse with results / Відповідь з результатами
        """
        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting receipt processing: {request.image_path}")

            # 2. LOAD IMAGE / ЗАВАНТАЖИТИ ЗОБРАЖЕННЯ
            image_data = await self._load_and_encode_image(request.image_path)
            logger.info(f"Image loaded: {len(image_data)} bytes")

            # 3. CALL OCR / ВИКЛИКАТИ OCR
            ocr_response = await self._call_openai_vision(image_data)
            logger.info(f"OCR response received: {len(ocr_response)} chars")

            # 4. PARSE RESULT / РОЗПАРСИТИ РЕЗУЛЬТАТ
            parsed_data = self._parse_ocr_response(ocr_response)
            logger.info(f"Parsed data: {json.dumps(parsed_data, indent=2, ensure_ascii=False)[:200]}...")

            # 5. VALIDATE / ВАЛІДУВАТИ
            receipt_result = ReceiptOCRResult(**parsed_data)
            logger.info(f"✓ Validation passed for {receipt_result.merchant_name}")

            # 6. SAVE / ЗБЕРЕГТИ (можна додати збереження в БД)
            # await self._save_to_database(receipt_result, request.user_id)
            # logger.info("Receipt saved to database")

            # 7. RETURN RESULT / ПОВЕРНУТИ РЕЗУЛЬТАТ
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            return ReceiptProcessingResponse(
                success=True,
                data=receipt_result,
                processing_time_ms=processing_time_ms
            )

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return self._error_response(f"File not found: {request.image_path}", start_time)

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return self._error_response(f"Invalid receipt data: {str(e)}", start_time)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._error_response(f"Processing failed: {str(e)}", start_time)

    async def _load_and_encode_image(self, image_path: str) -> str:
        """
        Load image and encode to base64 / Завантажити та кодувати зображення

        Args:
            image_path: Path to image file / Шлях до файлу

        Returns:
            Base64 encoded image / Зображення в base64
        """
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check file format / Перевірити формат
        valid_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        if path.suffix.lower() not in valid_formats:
            raise ValueError(f"Invalid format: {path.suffix}. Allowed: {valid_formats}")

        with open(path, 'rb') as f:
            image_bytes = f.read()

        return base64.b64encode(image_bytes).decode('utf-8')

    async def _call_openai_vision(self, image_data: str) -> str:
        """
        Call OpenAI Vision API / Викликати OpenAI Vision API

        Args:
            image_data: Base64 encoded image / Зображення в base64

        Returns:
            JSON response as string / JSON відповідь
        """
        prompt = """
Extract receipt information and return ONLY valid JSON with this structure:
{
    "merchant_name": "Store name",
    "merchant_address": "Address or null",
    "receipt_date": "2024-05-28T14:30:00",
    "receipt_number": "Number or null",
    "items": [
        {
            "name": "Product name",
            "quantity": 1,
            "unit_price": 25.00,
            "total_price": 25.00
        }
    ],
    "subtotal": 100.00,
    "tax_amount": 12.00,
    "total_amount": 112.00,
    "payment_method": "card or cash or null",
    "currency": "UAH"
}

RULES:
- Use ISO 8601 format for dates: YYYY-MM-DDTHH:MM:SS
- All prices as floats
- Use actual currency from receipt (default UAH)
- Items list must have at least one item
- Total should equal subtotal + tax
- Return ONLY the JSON, no explanations
"""

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",  # або gpt-4-vision
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        )

        return response.content[0].text

    def _parse_ocr_response(self, response: str) -> dict:
        """
        Parse OCR response / Розпарсити OCR відповідь

        Args:
            response: Raw response from API / Сира відповідь від API

        Returns:
            Parsed dictionary / Розпарсений словник
        """
        try:
            # Extract JSON from response / Виділити JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start == -1:
                raise ValueError("No JSON found in response")

            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            logger.info("JSON parsed successfully")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise ValueError(f"Invalid JSON in OCR response: {e}")

    def _error_response(
        self,
        error_msg: str,
        start_time: datetime
    ) -> ReceiptProcessingResponse:
        """Create error response / Створити помилкову відповідь"""
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ReceiptProcessingResponse(
            success=False,
            error=error_msg,
            processing_time_ms=processing_time_ms
        )


# ============================================================================
# USAGE EXAMPLE / ПРИКЛАД ВИКОРИСТАННЯ
# ============================================================================

async def main():
    """Example usage / Приклад використання"""

    service = ReceiptProcessingService(api_key="your-openai-api-key")

    # Create processing request / Створити запит
    request = ReceiptProcessingRequest(
        image_path="./receipt_image.jpg",
        user_id="user_123",
        extract_items=True
    )

    # Process receipt / Обробити чек
    response = await service.process_receipt(request)

    # Check result / Перевірити результат
    if response.success:
        print(f"✓ Receipt processed successfully!")
        print(f"  Merchant: {response.data.merchant_name}")
        print(f"  Total: {response.data.total_amount} {response.data.currency}")
        print(f"  Items: {len(response.data.items)}")
        print(f"  Time: {response.processing_time_ms:.2f}ms")
    else:
        print(f"✗ Processing failed: {response.error}")


if __name__ == "__main__":
    asyncio.run(main())
