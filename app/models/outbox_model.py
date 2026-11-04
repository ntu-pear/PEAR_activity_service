from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from datetime import datetime
from enum import Enum
from app.database import Base
import uuid
import json
from typing import Dict, Any


# How many publish attempts an event gets before it is given up on.
MAX_RETRY_ATTEMPTS = 3


class OutboxStatus(str, Enum):
    """Status enumeration"""
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"        # publish failed, attempts remain, will be retried
    ABANDONED = "ABANDONED"  # out of attempts, needs a human


class OutboxEvent(Base):
    """
    Outbox Event for guaranteed message delivery.
    Uses correlation_id for both traceability and deduplication.
    """
    __tablename__ = "OUTBOX_EVENTS"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(String(50), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON string
    routing_key = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default=OutboxStatus.PENDING, index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(String(1000))
    correlation_id = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
    processed_at = Column(DateTime)
    created_by = Column(String(255), nullable=False)

    def set_payload(self, data: Dict[str, Any]) -> None:
        """Set payload as JSON string"""
        self.payload = json.dumps(data, default=str, ensure_ascii=False)

    def get_payload(self) -> Dict[str, Any]:
        """Get payload as dictionary"""
        try:
            return json.loads(self.payload) if self.payload else {}
        except json.JSONDecodeError:
            return {}

    def mark_published(self) -> None:
        """Mark as successfully published"""
        self.status = OutboxStatus.PUBLISHED
        self.processed_at = datetime.now()
        self.error_message = None

    def mark_failed(self, error: str) -> None:
        """Record a failed publish attempt.

        FAILED means "failed but retryable". Once the attempts are used up
        the event becomes ABANDONED, which the publisher skips.

        This distinction matters: the publisher selects on status, so if
        every failure landed in one terminal state a single bad attempt
        would strand the event permanently. That is what happened to 42
        events between April and August 2026, each with retry_count = 1.
        """
        self.retry_count += 1
        self.error_message = error[:1000] if error else None
        self.status = (
            OutboxStatus.FAILED if self.can_retry() else OutboxStatus.ABANDONED
        )

    def can_retry(self) -> bool:
        """Whether any publish attempts remain."""
        return self.retry_count < MAX_RETRY_ATTEMPTS

    def __repr__(self):
        return f"<OutboxEvent(id={self.id}, type={self.event_type}, correlation_id={self.correlation_id})>"