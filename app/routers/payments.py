
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Payment, AuditLog, PaymentReview
from app.schemas import PaymentCreate, PaymentUpdate, RejectRequest
from app.services import payment_service as service
from app.config import ALLOW_TEST_DATE_OVERRIDE

router = APIRouter(prefix="/payments", tags=["Payments"])


def request_time(x_test_date: str | None):
    if x_test_date and not ALLOW_TEST_DATE_OVERRIDE:
        raise HTTPException(
            status_code=403,
            detail="Test date override is disabled"
        )

    return service.effective_now(x_test_date)


@router.post("", status_code=201)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    x_test_date: str | None = Header(default=None, alias="X-Test-Date")
):
    payment = service.create_payment(
        db, actor, payload, request_time(x_test_date)
    )
    return service.payment_dict(payment, db)


@router.get("")
def list_payments(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user)
):
    stmt = select(Payment)

    if status:
        stmt = stmt.where(Payment.status == status.upper())

    if "Admin" not in actor.roles:

        # Users with both Maker and Checker roles:
        # 1. See all their own payments.
        # 2. See other Makers' SUBMITTED payments.
        if "Maker" in actor.roles and "Checker" in actor.roles:
            stmt = stmt.where(
                or_(
                    Payment.maker_id == actor.user_id,
                    and_(
                        Payment.status == "SUBMITTED",
                        Payment.maker_id != actor.user_id
                    )
                )
            )

        # Checker-only users see other Makers' SUBMITTED payments.
        elif "Checker" in actor.roles:
            stmt = stmt.where(
                Payment.status == "SUBMITTED",
                Payment.maker_id != actor.user_id
            )

        # Maker-only users see their own payments.
        elif "Maker" in actor.roles:
            stmt = stmt.where(
                Payment.maker_id == actor.user_id
            )

        else:
            return []

    payments = db.scalars(
        stmt.order_by(Payment.id.desc())
    ).all()

    return [
        service.payment_dict(payment, db)
        for payment in payments
    ]


@router.get("/{payment_id}")
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user)
):
    payment = service.get_payment(db, payment_id)

    if (
        "Admin" not in actor.roles
        and payment.maker_id != actor.user_id
        and "Checker" not in actor.roles
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot view this payment"
        )

    return service.payment_dict(payment, db)


@router.put("/{payment_id}")
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    x_test_date: str | None = Header(default=None, alias="X-Test-Date")
):
    payment = service.update_payment(
        db, payment_id, actor, payload, request_time(x_test_date)
    )
    return service.payment_dict(payment, db)


@router.post("/{payment_id}/submit")
def submit_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    x_test_date: str | None = Header(default=None, alias="X-Test-Date")
):
    payment = service.submit_payment(
        db, payment_id, actor, request_time(x_test_date)
    )
    return service.payment_dict(payment, db)


@router.post("/{payment_id}/approve")
def approve_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    x_test_date: str | None = Header(default=None, alias="X-Test-Date")
):
    payment = service.approve_payment(
        db, payment_id, actor, request_time(x_test_date)
    )
    return service.payment_dict(payment, db)


@router.post("/{payment_id}/reject")
def reject_payment(
    payment_id: int,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    x_test_date: str | None = Header(default=None, alias="X-Test-Date")
):
    payment = service.reject_payment(
        db, payment_id, actor, payload.reason, request_time(x_test_date)
    )
    return service.payment_dict(payment, db)


@router.post("/{payment_id}/release")
def release_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    x_test_date: str | None = Header(default=None, alias="X-Test-Date")
):
    payment = service.release_payment(
        db, payment_id, actor, request_time(x_test_date)
    )
    return service.payment_dict(payment, db)


@router.get("/{payment_id}/audit")
def get_audit(
    payment_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user)
):
    payment = service.get_payment(db, payment_id)

    if (
        "Admin" not in actor.roles
        and payment.maker_id != actor.user_id
        and "Checker" not in actor.roles
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot view this audit trail"
        )

    entries = db.scalars(
        select(AuditLog)
        .where(AuditLog.payment_id == payment_id)
        .order_by(AuditLog.id)
    ).all()

    return [
        {
            "id": entry.id,
            "payment_id": entry.payment_id,
            "user_id": entry.user_id,
            "action": entry.action,
            "state_before": entry.state_before,
            "state_after": entry.state_after,
            "timestamp": entry.timestamp.isoformat(),
            "details": entry.details
        }
        for entry in entries
    ]
