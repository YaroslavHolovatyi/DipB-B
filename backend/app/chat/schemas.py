"""Pydantic schemas for chat."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ConversationType = Literal["direct", "group"]
PresenceStatus = Literal["online", "away", "offline"]


class Attachment(BaseModel):
    url: str
    type: str
    name: str | None = None
    size: int | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ConversationType
    title: str | None = None
    image_url: str | None = None
    friend_group_id: int | None = None
    raid_id: int | None = None
    last_message_at: datetime | None = None
    participants: list[int] = Field(default_factory=list)
    unread_count: int = 0
    last_message_preview: str | None = None


class ConversationCreate(BaseModel):
    """Either start a direct chat with one user, or a group chat with many."""

    type: ConversationType
    participant_ids: list[int] = Field(min_length=1)
    title: str | None = Field(default=None, max_length=80)
    friend_group_id: int | None = None

    @model_validator(mode="after")
    def _check(self) -> "ConversationCreate":
        if self.type == "direct" and len(self.participant_ids) != 1:
            raise ValueError("direct chats need exactly one other participant")
        return self


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    body: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)
    reply_to_id: int | None = None
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime
    reactions: dict[str, list[int]] = Field(default_factory=dict)  # emoji -> [user_id]


class MessageCreate(BaseModel):
    body: str | None = Field(default=None, max_length=4000)
    attachments: list[Attachment] = Field(default_factory=list)
    reply_to_id: int | None = None

    @model_validator(mode="after")
    def _require_content(self) -> "MessageCreate":
        if not (self.body or self.attachments):
            raise ValueError("message must have body or attachments")
        return self


class MessageEdit(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ReactionToggle(BaseModel):
    emoji: str = Field(min_length=1, max_length=32)


class PresenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    status: PresenceStatus
    last_seen_at: datetime


class MarkReadRequest(BaseModel):
    up_to_message_id: int


class TypingFrame(BaseModel):
    """Body of the `typing` event the client sends over the WS."""

    conversation_id: int
    is_typing: bool


# Re-exported so type checkers see Any imported.
__all__ = [
    "Attachment", "ConversationRead", "ConversationCreate", "MessageRead",
    "MessageCreate", "MessageEdit", "ReactionToggle", "PresenceRead",
    "MarkReadRequest", "TypingFrame", "Any",
]
