"""
Reusable SQLAlchemy column types for the project's native PostgreSQL enums.

Every enum here already exists in the database (created in
``database/schema.sql`` or a migration), so each type is declared with
``create_type=False`` — SQLAlchemy must NOT try to CREATE/DROP it.

WHY THIS MODULE EXISTS
----------------------
If an enum column is mapped as plain ``String``/``Text``, every comparison or
insert binds the value as ``VARCHAR``. PostgreSQL has no implicit
``enum = varchar`` operator, so queries fail at runtime with::

    operator does not exist: <enum_type> = character varying

Mapping the column to the matching ``ENUM`` below makes SQLAlchemy bind the
value as ``::<enum_type>`` instead, which Postgres accepts.

A single type instance is intentionally shared across every column/table that
uses it (e.g. ``drink_type`` on drinks, raid_drinks and party_drinks). With
``create_type=False`` this is safe — no duplicate DDL is emitted.

Label lists must stay in sync with the database. Where a migration added
values via ``ALTER TYPE ... ADD VALUE`` after the baseline, those values are
included here (and noted) so the ORM can read and write them.
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import ENUM


def _pg_enum(name: str, *labels: str) -> ENUM:
    """A reference to an existing native PG enum (never creates the type)."""
    return ENUM(*labels, name=name, create_type=False)


# --- Users / auth ---------------------------------------------------------- #
user_role = _pg_enum("user_role", "user", "admin", "moderator")
push_platform = _pg_enum("push_platform", "ios", "android", "web")
# Added by migration 0007_user_gender. Drives the m/f race avatar on profiles.
gender = _pg_enum("gender", "m", "f")

# --- Bars / drinks --------------------------------------------------------- #
price_category = _pg_enum("price_category", "budget", "mid", "premium", "luxury")
drink_type = _pg_enum(
    "drink_type", "beer", "cocktail", "wine", "spirit", "non_alcoholic", "other"
)

# --- Friends --------------------------------------------------------------- #
friendship_status = _pg_enum("friendship_status", "pending", "accepted", "blocked")
friend_request_status = _pg_enum(
    "friend_request_status", "pending", "accepted", "declined", "cancelled"
)
friend_group_role = _pg_enum("friend_group_role", "member", "admin")

# --- Raids ----------------------------------------------------------------- #
# 'aborted' added by migration 0003_raid_lifecycle.
raid_status = _pg_enum(
    "raid_status", "planned", "ongoing", "completed", "cancelled", "aborted"
)
# 'arrived', 'attended', 'no_show' added by migration 0003_raid_lifecycle.
raid_rsvp_status = _pg_enum(
    "raid_rsvp_status",
    "going",
    "maybe",
    "declined",
    "arrived",
    "attended",
    "no_show",
)
raid_visibility = _pg_enum("raid_visibility", "open", "friends_only")

# --- Parties --------------------------------------------------------------- #
party_visibility = _pg_enum("party_visibility", "open", "friends_only")
party_status = _pg_enum("party_status", "open", "closed", "cancelled")
party_member_status = _pg_enum("party_member_status", "joined", "left", "invited")

# --- Checks / dice --------------------------------------------------------- #
check_payment_method = _pg_enum(
    "check_payment_method", "d20_dice", "voluntary", "agreement", "split"
)
check_participant_status = _pg_enum(
    "check_participant_status", "invited", "joined", "ready", "left"
)
dice_proposal_status = _pg_enum(
    "dice_proposal_status", "pending", "accepted", "declined", "completed", "cancelled"
)
dice_vote = _pg_enum("dice_vote", "pending", "accept", "decline")

# --- Chat ------------------------------------------------------------------ #
conversation_type = _pg_enum("conversation_type", "direct", "group")
conversation_role = _pg_enum("conversation_role", "member", "admin")
presence_status = _pg_enum("presence_status", "online", "away", "offline")

# --- Achievements / notifications ------------------------------------------ #
achievement_category = _pg_enum(
    "achievement_category",
    "social",
    "exploration",
    "spending",
    "quiz",
    "kind_soul",
    "misc",
)
# 'party_invite' added by migration 0004_parties.
notification_type = _pg_enum(
    "notification_type",
    "friend_request",
    "friend_accepted",
    "raid_invite",
    "raid_reminder",
    "achievement_unlocked",
    "check_shared",
    "check_invite",
    "check_split_completed",
    "dice_proposal_created",
    "dice_proposal_resolved",
    "kind_soul_awarded",
    "dnd_session_reminder",
    "system",
    "party_invite",
)

# --- Tavern Tales (D&D) ---------------------------------------------------- #
dnd_class = _pg_enum(
    "dnd_class",
    "barbarian",
    "bard",
    "cleric",
    "druid",
    "fighter",
    "monk",
    "paladin",
    "ranger",
    "rogue",
    "sorcerer",
    "warlock",
    "wizard",
)
dnd_alignment = _pg_enum(
    "dnd_alignment",
    "lawful_good",
    "neutral_good",
    "chaotic_good",
    "lawful_neutral",
    "true_neutral",
    "chaotic_neutral",
    "lawful_evil",
    "neutral_evil",
    "chaotic_evil",
)
dnd_mode = _pg_enum("dnd_mode", "munchkin", "normal", "dungeon_master_pro")
dnd_session_status = _pg_enum(
    "dnd_session_status", "active", "paused", "completed", "abandoned"
)
dnd_message_role = _pg_enum(
    "dnd_message_role", "user", "assistant", "system", "dice_roll", "narration"
)
