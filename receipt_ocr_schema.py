"""
Receipt OCR Processing Schema and Models
Схема обробки квитків OCR та моделі
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


# ============================================================================
# PYDANTIC MODELS / МОДЕЛІ PYDANTIC
# ============================================================================

class ReceiptItem(BaseModel):
    """Individual receipt item / Окремий товар на квитку"""
    name: str = Field(..., description="Product name / Назва товару")
    quantity: float = Field(..., gt=0, description="Quantity / Кількість")
    unit_price: Decimal = Field(..., gt=0, description="Price per unit / Ціна за одиницю")
    total_price: Decimal = Field(..., gt=0, description="Total for item / Сума за товар")

    class Config:
        json_encoders = {Decimal: float}


class ReceiptOCRResult(BaseModel):
    """
    Receipt OCR extraction result
    Результат обробки квитка через OCR
    """
    # Merchant info / Інформація про магазин
    merchant_name: str = Field(..., description="Store/merchant name / Назва магазину")
    merchant_address: Optional[str] = Field(None, description="Store address / Адреса магазину")

    # Receipt metadata / Метадані квитка
    receipt_date: datetime = Field(..., description="Receipt date and time / Дата та час квитка")
    receipt_number: Optional[str] = Field(None, description="Receipt number / Номер квитка")

    # Items / Товари
    items: List[ReceiptItem] = Field(..., min_items=1, description="List of items / Список товарів")

    # Totals / Суми
    subtotal: Decimal = Field(..., gt=0, description="Subtotal before tax / Сума без податку")
    tax_amount: Optional[Decimal] = Field(None, ge=0, description="Tax amount / Сума податку")
    total_amount: Decimal = Field(..., gt=0, description="Total amount / Сума до сплати")

    # Payment info / Інформація про оплату
    payment_method: Optional[str] = Field(None, description="Payment method / Спосіб оплати")
    currency: str = Field(default="UAH", description="Currency code / Код валюти")

    # Metadata / Метадані
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="OCR confidence / Впевненість OCR")
    ocr_model: str = Field(default="gpt-4-vision", description="Model used for OCR / Модель OCR")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing time / Час обробки")

    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }

    @validator('total_amount')
    def validate_total(cls, v, values):
        """Ensure total matches subtotal + tax"""
        if 'subtotal' not in values or 'tax_amount' not in values:
            return v

        subtotal = values.get('subtotal', 0)
        tax = values.get('tax_amount') or Decimal(0)
        expected_total = subtotal + tax

        # Allow small rounding differences
        if abs(v - expected_total) > Decimal('0.01'):
            raise ValueError(
                f'Total {v} does not match subtotal {subtotal} + tax {tax} = {expected_total}'
            )
        return v

    @validator('items')
    def validate_items_sum(cls, v, values):
        """Ensure items sum matches subtotal"""
        if not v or 'subtotal' not in values:
            return v

        items_total = sum(item.total_price for item in v)
        subtotal = values.get('subtotal', 0)

        if abs(items_total - subtotal) > Decimal('0.01'):
            raise ValueError(
                f'Items sum {items_total} does not match subtotal {subtotal}'
            )
        return v


class ReceiptProcessingRequest(BaseModel):
    """Request to process a receipt / Запит на обробку квитка"""
    image_path: str = Field(..., description="Path to receipt image / Шлях до зображення")
    user_id: Optional[str] = Field(None, description="User ID / ID користувача")
    extract_items: bool = Field(default=True, description="Extract individual items / Виділити товари")


class ReceiptProcessingResponse(BaseModel):
    """Response from receipt processing / Відповідь обробки квитка"""
    success: bool = Field(..., description="Processing success / Успіх обробки")
    data: Optional[ReceiptOCRResult] = Field(None, description="OCR result / Результат OCR")
    error: Optional[str] = Field(None, description="Error message / Повідомлення про помилку")
    processing_time_ms: float = Field(..., description="Time taken in milliseconds / Час обробки мс")


# ============================================================================
# EXAMPLE / ПРИКЛАД
# ============================================================================

EXAMPLE_RECEIPT = {
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
        },
        {
            "name": "Яйця (10 шт)",
            "quantity": 1,
            "unit_price": 45.00,
            "total_price": 45.00
        }
    ],
    "subtotal": 140.00,
    "tax_amount": 16.80,
    "total_amount": 156.80,
    "payment_method": "card",
    "currency": "UAH",
    "confidence_score": 0.95,
    "ocr_model": "gpt-4-vision"
}

if __name__ == "__main__":
    # Тестування моделі / Test the model
    result = ReceiptOCRResult(**EXAMPLE_RECEIPT)
    print("✓ Receipt model validation passed!")
    print(f"Total: {result.total_amount} {result.currency}")
    print(f"Items: {len(result.items)}")
    print(f"Confidence: {result.confidence_score}")
