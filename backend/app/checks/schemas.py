"""Pydantic schemas for the checks (receipts) + split room domain."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ParticipantStatus = Literal["invited", "joined", "ready", "left"]
ProposalStatus = Literal["pending", "accepted", "declined", "completed", "cancelled"]
Vote = Literal["pending", "accept", "decline"]


# --------------------------------------------------------------------------- #
# Items
# --------------------------------------------------------------------------- #
class CheckItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    position: int
    # Aggregated from assignments — sum of assigned quantity / amount.
    assigned_quantity: Decimal = Decimal("0")


class CheckItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)


# --------------------------------------------------------------------------- #
# Participants
# --------------------------------------------------------------------------- #
class CheckParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    display_name: str
    color: str | None = None
    status: ParticipantStatus
    joined_at: datetime | None = None
    ready_at: datetime | None = None
    subtotal: Decimal = Decimal("0")


class InviteParticipants(BaseModel):
    """Add registered or guest participants to an open check."""

    user_ids: list[int] = Field(default_factory=list)
    guests: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Assignments
# --------------------------------------------------------------------------- #
class ItemAssignmentUpsert(BaseModel):
    participant_id: int
    quantity: Decimal = Field(gt=0)


class ItemAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_item_id: int
    participant_id: int
    quantity: Decimal
    amount: Decimal


# --------------------------------------------------------------------------- #
# Check create / read
# --------------------------------------------------------------------------- #
class CheckCreate(BaseModel):
    """The phone hands us the uploaded image URL; the server triggers OCR."""

    image_url: str
    bar_id: int | None = None
    occurred_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)


class EventCheckCreate(BaseModel):
    """Create a check from a finished raid/party's shared bill.

    Exactly one of `raid_id` / `party_id` must be set; the server seeds the
    split room with the event's verified attendees.
    """

    image_url: str
    raid_id: int | None = None
    party_id: int | None = None
    occurred_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)


class ReceiptUploadRequest(BaseModel):
    content_type: str = Field(default="image/jpeg")


class ReceiptUploadResponse(BaseModel):
    """Presigned PUT URL the phone uploads the receipt photo to.

    Flow: POST /checks/upload-url → PUT the file to `upload_url` → POST /checks
    with `image_url = public_url`.
    """

    upload_url: str
    public_url: str
    key: str
    expires_in: int


class CheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bar_id: int | None = None
    raid_id: int | None = None
    party_id: int | None = None
    bar_name_freeform: str | None = None
    currency: str
    total_amount: Decimal
    image_url: str | None = None
    occurred_at: datetime | None = None
    note: str | None = None
    parsed_at: datetime | None = None
    created_at: datetime
    items: list[CheckItemRead] = Field(default_factory=list)
    participants: list[CheckParticipantRead] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Dice
# --------------------------------------------------------------------------- #
class DiceProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    check_id: int
    proposed_by: int
    status: ProposalStatus
    decided_at: datetime | None = None
    cancel_reason: str | None = None
    created_at: datetime
    votes: list["DiceVoteRead"] = Field(default_factory=list)


class DiceVoteRead(BaseModel):
    user_id: int
    vote: Vote
    voted_at: datetime | None = None


class DiceVoteCast(BaseModel):
    vote: Literal["accept", "decline"]


class KindSoulEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    check_id: int
    payer_user_id: int
    total_paid_for_others: Decimal
    decided_via: str
    event_metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


class KindSoulLeaderRow(BaseModel):
    user_id: int
    first_name: str
    username: str
    avatar_url: str | None = None
    events_count: int
    total_paid_for_others: Decimal


DiceProposalRead.model_rebuild()
