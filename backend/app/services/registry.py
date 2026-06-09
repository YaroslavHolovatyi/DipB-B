"""
Service registry.

A tiny indirection over the build_* factories. Holding instances on a module
gives us:

    1. One shared client per service (so we don't re-open HTTP connections).
    2. A single place to override services in tests
       (`registry.set_push_service(FakePushService())`).
    3. FastAPI dependencies that just return the cached instance.
"""

from __future__ import annotations

from app.services.llm import LlmService, build_llm_service
from app.services.ocr import OcrService, build_ocr_service
from app.services.push import PushService, build_push_service
from app.services.storage import StorageService, build_storage_service


class _ServiceRegistry:
    ocr: OcrService
    storage: StorageService
    push: PushService
    llm: LlmService

    def __init__(self) -> None:
        self.ocr = build_ocr_service()
        self.storage = build_storage_service()
        self.push = build_push_service()
        self.llm = build_llm_service()


_registry = _ServiceRegistry()


# --------------------------------------------------------------------------- #
# Accessors used as FastAPI dependencies
# --------------------------------------------------------------------------- #
def get_ocr_service() -> OcrService:
    return _registry.ocr


def get_storage_service() -> StorageService:
    return _registry.storage


def get_push_service() -> PushService:
    return _registry.push


def get_llm_service() -> LlmService:
    return _registry.llm


# --------------------------------------------------------------------------- #
# Test overrides — not used in production code paths
# --------------------------------------------------------------------------- #
def set_ocr_service(service: OcrService) -> None:
    _registry.ocr = service


def set_storage_service(service: StorageService) -> None:
    _registry.storage = service


def set_push_service(service: PushService) -> None:
    _registry.push = service


def set_llm_service(service: LlmService) -> None:
    _registry.llm = service
