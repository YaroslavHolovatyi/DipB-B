"""
FastAPI Endpoints for Receipt OCR Processing
FastAPI endpoints для обробки квітків OCR
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import tempfile
from pathlib import Path
import logging

from receipt_ocr_schema import (
    ReceiptOCRResult,
    ReceiptProcessingRequest,
    ReceiptProcessingResponse
)
from receipt_processing_workflow import ReceiptProcessingService

logger = logging.getLogger(__name__)

# Initialize router / Ініціалізувати маршрутизатор
router = APIRouter(prefix="/api/receipts", tags=["Receipts"])

# Initialize service / Ініціалізувати сервіс
receipt_service = ReceiptProcessingService()


# ============================================================================
# ENDPOINTS / ENDPOINTS
# ============================================================================

@router.post(
    "/process",
    response_model=ReceiptProcessingResponse,
    summary="Process receipt image",
    description="Обробити зображення квітка за допомогою OpenAI Vision"
)
async def process_receipt_image(
    file: UploadFile = File(..., description="Receipt image file / Файл зображення квітка"),
    user_id: str = None
) -> ReceiptProcessingResponse:
    """
    Upload and process a receipt image

    Послідовність:
    1. Завантажити файл / Upload file
    2. Зберегти тимчасово / Save temporarily
    3. Обробити через OpenAI / Process via OpenAI
    4. Повернути результат / Return result

    Example / Приклад:
    ```bash
    curl -X POST "http://localhost:8000/api/receipts/process" \\
      -F "file=@receipt.jpg" \\
      -F "user_id=user_123"
    ```
    """

    try:
        # Validate file type / Перевірити тип файлу
        allowed_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
            )

        # Save temporarily / Зберегти тимчасово
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            # Create request / Створити запит
            request = ReceiptProcessingRequest(
                image_path=tmp_path,
                user_id=user_id,
                extract_items=True
            )

            # Process / Обробити
            response = await receipt_service.process_receipt(request)

            logger.info(
                f"Receipt processed: success={response.success}, "
                f"time={response.processing_time_ms:.2f}ms"
            )

            return response

        finally:
            # Cleanup / Очистити
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process receipt: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=dict,
    summary="Validate receipt data",
    description="Перевірити формат даних квітка"
)
async def validate_receipt_data(data: dict) -> dict:
    """
    Validate receipt data structure without OCR

    Перевірити дані квітка без OCR

    Example / Приклад:
    ```json
    {
        "merchant_name": "SuperMarket ABC",
        "receipt_date": "2024-05-28T14:30:00",
        "items": [...],
        "total_amount": 156.80,
        ...
    }
    ```
    """

    try:
        result = ReceiptOCRResult(**data)
        return {
            "valid": True,
            "message": "Receipt data is valid",
            "data": result.dict()
        }

    except Exception as e:
        return {
            "valid": False,
            "message": f"Validation failed: {str(e)}",
            "errors": str(e)
        }


@router.get(
    "/example",
    response_model=dict,
    summary="Get example receipt",
    description="Отримати приклад структури квітка"
)
async def get_example_receipt() -> dict:
    """
    Get example receipt structure for reference

    Отримати приклад структури квітка як еталон
    """
    return {
        "example": {
            "merchant_name": "SuperMarket ABC",
            "merchant_address": "вул. Головна, 123, Київ",
            "receipt_date": "2024-05-28T14:30:00",
            "receipt_number": "001234",
            "items": [
                {
                    "name": "Хліб пшеничний",
                    "quantity": 1,
                    "unit_price": 25.00,
                    "total_price": 25.00
                },
                {
                    "name": "Молоко 1л",
                    "quantity": 2,
                    "unit_price": 35.00,
                    "total_price": 70.00
                }
            ],
            "subtotal": 95.00,
            "tax_amount": 11.40,
            "total_amount": 106.40,
            "payment_method": "card",
            "currency": "UAH",
            "confidence_score": 0.95
        },
        "description": "Example receipt structure / Приклад структури квітка",
        "required_fields": [
            "merchant_name",
            "receipt_date",
            "items",
            "subtotal",
            "total_amount",
            "currency"
        ]
    }


# ============================================================================
# HELPER FUNCTIONS / ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================================

async def get_receipt_service() -> ReceiptProcessingService:
    """Dependency for receipt service / Залежність для сервісу"""
    return receipt_service


# ============================================================================
# INTEGRATION WITH MAIN APP / ІНТЕГРАЦІЯ З ОСНОВНОЮ ПРОГРАМОЮ
# ============================================================================

"""
Usage in main FastAPI app / Використання в основній FastAPI програмі:

from fastapi import FastAPI
from receipt_api_endpoints import router

app = FastAPI(title="My App with Receipt OCR")

# Include receipt routes / Включити маршрути для квітків
app.include_router(router)

# Run with: uvicorn main:app --reload
"""


# ============================================================================
# CURL EXAMPLES / ПРИКЛАДИ CURL
# ============================================================================

"""
1. Process receipt image / Обробити зображення квітка:
   curl -X POST "http://localhost:8000/api/receipts/process" \\
     -F "file=@receipt.jpg" \\
     -F "user_id=user_123"

2. Validate data / Перевірити дані:
   curl -X POST "http://localhost:8000/api/receipts/validate" \\
     -H "Content-Type: application/json" \\
     -d '{
       "merchant_name": "Store",
       "receipt_date": "2024-05-28T14:30:00",
       "items": [{"name": "Item", "quantity": 1, "unit_price": 10, "total_price": 10}],
       "subtotal": 10,
       "total_amount": 10,
       "currency": "UAH"
     }'

3. Get example / Отримати приклад:
   curl http://localhost:8000/api/receipts/example

4. Using HTTPie / Використовуючи HTTPie:
   http -F POST localhost:8000/api/receipts/process file@receipt.jpg user_id=user_123
"""
