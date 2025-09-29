"""Business logic for messaging operations."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, aliased, joinedload

from ..errors import (
    AuthorizationError,
    ConversationExistsError,
    ConversationNotFoundError,
    ValidationError,
)
from ..models import Conversation, ConversationParticipant, Message


class ConversationService:
    """High level conversation operations backed by SQLAlchemy."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Conversation queries
    # ------------------------------------------------------------------
    def list_conversations(self, user_id: int) -> list[dict[str, object]]:
        query: Select[tuple[Conversation]] = (
            select(Conversation)
            .options(
                joinedload(Conversation.participants),
                joinedload(Conversation.messages),
            )
            .join(ConversationParticipant)
            .where(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        )
        conversations = self.session.execute(query).unique().scalars().all()
        return [self._serialize_conversation(conv, user_id) for conv in conversations]

    def create_conversation(
        self, user_id: int, participant_id: int, initial_message: str | None = None
    ) -> dict[str, object]:
        if participant_id == user_id:
            raise ValidationError(
                "Validation échouée.", {"participant_id": ["Impossible de démarrer une conversation avec soi-même."]}
            )

        if participant_id <= 0:
            raise ValidationError(
                "Validation échouée.", {"participant_id": ["Identifiant du participant invalide."]}
            )

        if self._conversation_exists(user_id, participant_id):
            raise ConversationExistsError("Conversation déjà existante.")

        conversation = Conversation()
        self.session.add(conversation)
        self.session.flush()

        creator_participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id,
            last_read_at=_utcnow(),
        )
        other_participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=participant_id,
            last_read_at=None,
        )
        self.session.add_all([creator_participant, other_participant])

        message_obj: Message | None = None
        if initial_message is not None:
            text = initial_message.strip()
            if not text:
                raise ValidationError(
                    "Validation échouée.", {"initial_message": ["Le message initial ne peut pas être vide."]}
                )
            if len(text) > 1000:
                raise ValidationError(
                    "Validation échouée.", {"initial_message": ["Le message initial dépasse 1000 caractères."]}
                )
            message_obj = Message(
                conversation_id=conversation.id,
                sender_id=user_id,
                text=text,
                created_at=_utcnow(),
            )
            self.session.add(message_obj)
            creator_participant.last_read_at = message_obj.created_at
            conversation.updated_at = message_obj.created_at

        self.session.flush()
        self.session.commit()
        return self._serialize_conversation(conversation, user_id, last_message_override=message_obj)

    def get_messages(self, conversation_id: int, user_id: int) -> list[dict[str, object]]:
        conversation, _ = self._ensure_participant(conversation_id, user_id)
        query = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        messages = self.session.scalars(query).all()
        return [self._serialize_message(msg) for msg in messages]

    def send_message(self, conversation_id: int, user_id: int, text: str) -> dict[str, object]:
        conversation, participant = self._ensure_participant(conversation_id, user_id)
        cleaned = text.strip()
        if not cleaned:
            raise ValidationError("Validation échouée.", {"text": ["Le message ne peut pas être vide."]})
        if len(cleaned) > 1000:
            raise ValidationError(
                "Validation échouée.", {"text": ["Le message ne peut pas dépasser 1000 caractères."]}
            )

        message = Message(
            conversation_id=conversation.id,
            sender_id=user_id,
            text=cleaned,
            created_at=_utcnow(),
        )
        self.session.add(message)
        participant.last_read_at = message.created_at
        conversation.updated_at = message.created_at
        self.session.flush()
        self.session.commit()
        return self._serialize_message(message)

    def mark_read(self, conversation_id: int, user_id: int) -> None:
        _, participant = self._ensure_participant(conversation_id, user_id)
        participant.last_read_at = _utcnow()
        self.session.flush()
        self.session.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _conversation_exists(self, user_a: int, user_b: int) -> bool:
        cp1 = aliased(ConversationParticipant)
        cp2 = aliased(ConversationParticipant)
        query = (
            select(Conversation.id)
            .join(cp1, (cp1.conversation_id == Conversation.id) & (cp1.user_id == user_a))
            .join(cp2, (cp2.conversation_id == Conversation.id) & (cp2.user_id == user_b))
        )
        return self.session.execute(query).first() is not None

    def _ensure_participant(
        self, conversation_id: int, user_id: int
    ) -> tuple[Conversation, ConversationParticipant]:
        query = (
            select(Conversation)
            .options(joinedload(Conversation.participants))
            .where(Conversation.id == conversation_id)
        )
        conversation = self.session.execute(query).unique().scalars().first()
        if conversation is None:
            raise ConversationNotFoundError("Conversation introuvable pour l'identifiant fourni.")

        participant = next((p for p in conversation.participants if p.user_id == user_id), None)
        if participant is None:
            raise AuthorizationError("Accès refusé car l'utilisateur n'est pas autorisé à consulter cette conversation.")
        return conversation, participant

    def _serialize_conversation(
        self,
        conversation: Conversation,
        user_id: int,
        *,
        last_message_override: Message | None = None,
    ) -> dict[str, object]:
        other = next((p for p in conversation.participants if p.user_id != user_id), None)
        participant_state = next((p for p in conversation.participants if p.user_id == user_id), None)
        last_message = last_message_override
        if last_message is None and conversation.messages:
            last_message = conversation.messages[-1]

        unread_count = 0
        if participant_state is not None:
            last_read_at = participant_state.last_read_at
            for message in conversation.messages:
                if message.sender_id == user_id:
                    continue
                if last_read_at is None or message.created_at > last_read_at:
                    unread_count += 1

        payload: dict[str, object] = {
            "id": conversation.id,
            "participant_name": other.display_name if other else None,
            "participant_avatar": other.avatar_url if other else None,
            "unread_count": unread_count,
        }
        if last_message is not None:
            payload["last_message"] = {
                "text": last_message.text,
                "timestamp": last_message.created_at.isoformat().replace("+00:00", "Z"),
            }
        else:
            payload["last_message"] = None
        return payload

    def _serialize_message(self, message: Message) -> dict[str, object]:
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "text": message.text,
            "timestamp": message.created_at.isoformat().replace("+00:00", "Z"),
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
