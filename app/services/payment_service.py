
from datetime import datetime, date, time, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models import Payment, PaymentReview, AuditLog, User

IST = ZoneInfo("Asia/Kolkata")

APPROVAL_THRESHOLD_PAISE = 100_000_000  # Rs 10,00,000
DAILY_LIMIT_PAISE = 500_000_000         # Rs 50,00,000


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def effective_now(test_date: str | None = None) -> datetime:
    if test_date:
        try:
            d = date.fromisoformat(test_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="X-Test-Date must use YYYY-MM-DD"
            )

        return datetime.combine(
            d, time(12, 0), tzinfo=IST
        ).astimezone(timezone.utc)

    return now_utc()


def amount_to_paise(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1")))


def required_approvals(amount_paise: int) -> int:
    return 1 if amount_paise <= APPROVAL_THRESHOLD_PAISE else 2


def audit(
    db: Session,
    payment: Payment,
    actor: User,
    action: str,
    before: str | None,
    after: str,
    at: datetime,
    details: str | None = None
):
    db.add(
        AuditLog(
            payment_id=payment.id,
            user_id=actor.user_id,
            action=action,
            state_before=before,
            state_after=after,
            timestamp=at,
            details=details
        )
    )


def lock_sqlite_write(db: Session):
    # SQLite serializes writers. Begin the write transaction
    # before reading approval state.
    if db.bind and db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))


def get_payment(db: Session, payment_id: int) -> Payment:
    payment = db.get(Payment, payment_id)

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    return payment


def count_approvals(db: Session, payment_id: int) -> int:
    return db.scalar(
        select(func.count(PaymentReview.id)).where(
            PaymentReview.payment_id == payment_id,
            PaymentReview.decision == "APPROVE"
        )
    ) or 0


def payment_dict(payment: Payment, db: Session) -> dict:
    return {
        "id": payment.id,
        "maker_id": payment.maker_id,
        "beneficiary_name": payment.beneficiary_name,
        "beneficiary_id": payment.beneficiary_id,
        "amount": Decimal(payment.amount_paise) / Decimal(100),
        "purpose": payment.purpose,
        "status": payment.status,
        "created_at": payment.created_at.isoformat(),
        "submitted_at": (
            payment.submitted_at.isoformat()
            if payment.submitted_at else None
        ),
        "approvals_received": count_approvals(db, payment.id),
        "approvals_required": required_approvals(
            payment.amount_paise
        ),
    }


def create_payment(db: Session, actor: User, data, at: datetime):
    if "Maker" not in actor.roles:
        raise HTTPException(
            status_code=403,
            detail="Maker role is required"
        )

    lock_sqlite_write(db)

    payment = Payment(
        maker_id=actor.user_id,
        beneficiary_name=data.beneficiary_name.strip(),
        beneficiary_id=data.beneficiary_id.strip(),
        amount_paise=amount_to_paise(data.amount),
        purpose=data.purpose.strip(),
        status="DRAFT",
        created_at=at
    )

    db.add(payment)
    db.flush()

    audit(
        db, payment, actor, "CREATE",
        None, "DRAFT", at, "Payment created"
    )

    db.commit()
    db.refresh(payment)

    return payment


def update_payment(
    db: Session,
    payment_id: int,
    actor: User,
    data,
    at: datetime
):
    lock_sqlite_write(db)

    payment = get_payment(db, payment_id)

    if "Maker" not in actor.roles:
        raise HTTPException(
            status_code=403,
            detail="Maker role is required"
        )

    if payment.maker_id != actor.user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the maker who created this payment can edit it"
        )

    if payment.status not in ("DRAFT", "SUBMITTED"):
        raise HTTPException(
            status_code=409,
            detail="Only DRAFT or SUBMITTED payments can be edited"
        )

    before = payment.status

    payment.beneficiary_name = data.beneficiary_name.strip()
    payment.beneficiary_id = data.beneficiary_id.strip()
    payment.amount_paise = amount_to_paise(data.amount)
    payment.purpose = data.purpose.strip()

    if before == "SUBMITTED":
        payment.status = "DRAFT"
        payment.submitted_at = None

        for review in list(payment.reviews):
            db.delete(review)

    audit(
        db, payment, actor, "EDIT",
        before, payment.status, at,
        "Edited; approvals cleared and returned to DRAFT"
        if before == "SUBMITTED"
        else "Draft edited"
    )

    db.commit()
    db.refresh(payment)

    return payment


def submit_payment(
    db: Session,
    payment_id: int,
    actor: User,
    at: datetime
):
    lock_sqlite_write(db)

    payment = get_payment(db, payment_id)

    if "Maker" not in actor.roles:
        raise HTTPException(
            status_code=403,
            detail="Maker role is required"
        )

    if payment.maker_id != actor.user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the maker who created this payment can submit it"
        )

    if payment.status != "DRAFT":
        raise HTTPException(
            status_code=409,
            detail="Only DRAFT payments can be submitted"
        )

    # Determine the calendar date of the submission in IST.
    local_date = at.astimezone(IST).date()

    # Start of the submission day in IST, converted to UTC.
    start_ist = datetime.combine(
        local_date,
        time.min,
        tzinfo=IST
    )

    # Start of the following day in IST, converted to UTC.
    next_day_ist = datetime.combine(
        date.fromordinal(local_date.toordinal() + 1),
        time.min,
        tzinfo=IST
    )

    start_utc = start_ist.astimezone(timezone.utc).replace(
        tzinfo=None
    )

    next_day_utc = next_day_ist.astimezone(timezone.utc).replace(
        tzinfo=None
    )

    # Count only the maker's active submitted payments
    # within the current IST calendar day.
    total = db.scalar(
        select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
            Payment.maker_id == actor.user_id,
            Payment.submitted_at >= start_utc,
            Payment.submitted_at < next_day_utc,
            Payment.status.in_(
                ["SUBMITTED", "APPROVED", "RELEASED"]
            )
        )
    ) or 0

    if total + payment.amount_paise > DAILY_LIMIT_PAISE:
        raise HTTPException(
            status_code=409,
            detail="Daily submission limit of INR 50,00,000 would be exceeded"
        )

    before = payment.status

    payment.status = "SUBMITTED"
    payment.submitted_at = at

    audit(
        db, payment, actor, "SUBMIT",
        before, "SUBMITTED", at,
        "Payment submitted for approval"
    )

    db.commit()
    db.refresh(payment)

    return payment


def approve_payment(
    db: Session,
    payment_id: int,
    actor: User,
    at: datetime
):
    lock_sqlite_write(db)

    payment = get_payment(db, payment_id)

    if "Checker" not in actor.roles:
        raise HTTPException(
            status_code=403,
            detail="Only a Checker can approve or reject"
        )

    if payment.status != "SUBMITTED":
        raise HTTPException(
            status_code=409,
            detail="Only SUBMITTED payments can be approved"
        )

    if payment.maker_id == actor.user_id:
        raise HTTPException(
            status_code=403,
            detail="Maker cannot approve their own payment"
        )

    if db.scalar(
        select(PaymentReview.id).where(
            PaymentReview.payment_id == payment.id,
            PaymentReview.checker_id == actor.user_id
        )
    ):
        raise HTTPException(
            status_code=409,
            detail="This checker has already reviewed this payment"
        )

    before = payment.status

    db.add(
        PaymentReview(
            payment_id=payment.id,
            checker_id=actor.user_id,
            decision="APPROVE",
            created_at=at
        )
    )

    db.flush()

    approvals = count_approvals(db, payment.id)
    required = required_approvals(payment.amount_paise)

    if approvals >= required:
        payment.status = "APPROVED"

    audit(
        db, payment, actor, "APPROVE",
        before, payment.status, at,
        f"Approval {approvals} of {required}"
    )

    db.commit()
    db.refresh(payment)

    return payment


def reject_payment(
    db: Session,
    payment_id: int,
    actor: User,
    reason: str,
    at: datetime
):
    lock_sqlite_write(db)

    payment = get_payment(db, payment_id)

    if "Checker" not in actor.roles:
        raise HTTPException(
            status_code=403,
            detail="Only a Checker can approve or reject"
        )

    if payment.status != "SUBMITTED":
        raise HTTPException(
            status_code=409,
            detail="Only SUBMITTED payments can be rejected"
        )

    if payment.maker_id == actor.user_id:
        raise HTTPException(
            status_code=403,
            detail="Maker cannot reject their own payment"
        )

    if db.scalar(
        select(PaymentReview.id).where(
            PaymentReview.payment_id == payment.id,
            PaymentReview.checker_id == actor.user_id
        )
    ):
        raise HTTPException(
            status_code=409,
            detail="This checker has already reviewed this payment"
        )

    before = payment.status

    db.add(
        PaymentReview(
            payment_id=payment.id,
            checker_id=actor.user_id,
            decision="REJECT",
            reason=reason.strip(),
            created_at=at
        )
    )

    payment.status = "REJECTED"

    audit(
        db, payment, actor, "REJECT",
        before, "REJECTED", at, reason.strip()
    )

    db.commit()
    db.refresh(payment)

    return payment


def release_payment(
    db: Session,
    payment_id: int,
    actor: User,
    at: datetime
):
    lock_sqlite_write(db)

    payment = get_payment(db, payment_id)

    if "Admin" not in actor.roles:
        raise HTTPException(
            status_code=403,
            detail="Admin role is required"
        )

    if payment.status != "APPROVED":
        raise HTTPException(
            status_code=409,
            detail="Only APPROVED payments can be released"
        )

    before = payment.status

    payment.status = "RELEASED"

    audit(
        db, payment, actor, "RELEASE",
        before, "RELEASED", at,
        "Release simulated; no money transferred"
    )

    db.commit()
    db.refresh(payment)

    return payment
