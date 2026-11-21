from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.database import Base

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    roles: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    maker_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    beneficiary_name: Mapped[str] = mapped_column(String(200), nullable=False)
    beneficiary_id: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purpose: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    reviews: Mapped[list["PaymentReview"]] = relationship(back_populates="payment", cascade="all, delete-orphan")
    audit_entries: Mapped[list["AuditLog"]] = relationship(back_populates="payment")

class PaymentReview(Base):
    __tablename__ = "payment_reviews"
    __table_args__ = (UniqueConstraint("payment_id", "checker_id", name="uq_payment_checker"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False, index=True)
    checker_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment: Mapped["Payment"] = relationship(back_populates="reviews")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    state_before: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state_after: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment: Mapped["Payment"] = relationship(back_populates="audit_entries")
