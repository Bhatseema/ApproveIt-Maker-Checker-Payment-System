def headers(user):
    return {"X-User-Id": user, "X-Test-Date": "2026-11-15"}

def payload(amount=500000):
    return {
        "beneficiary_name": "ABC Technologies",
        "beneficiary_id": "BEN001",
        "amount": amount,
        "purpose": "Vendor payment"
    }

def create_and_submit(client, amount=500000, maker="M1"):
    r = client.post("/payments", json=payload(amount), headers=headers(maker))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    r = client.post(f"/payments/{pid}/submit", headers=headers(maker))
    assert r.status_code == 200, r.text
    return pid

def test_create_submit_and_one_approval_release(client):
    pid = create_and_submit(client, 500000)
    r = client.post(f"/payments/{pid}/approve", headers=headers("C1"))
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"
    r = client.post(f"/payments/{pid}/release", headers=headers("A1"))
    assert r.status_code == 200
    assert r.json()["status"] == "RELEASED"

def test_high_value_needs_two_checkers(client):
    pid = create_and_submit(client, 1500000)
    r = client.post(f"/payments/{pid}/approve", headers=headers("C1"))
    assert r.status_code == 200
    assert r.json()["status"] == "SUBMITTED"
    r = client.post(f"/payments/{pid}/approve", headers=headers("C2"))
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

def test_maker_cannot_approve_own_payment_even_if_checker(client):
    pid = create_and_submit(client, 500000, "MC1")
    r = client.post(f"/payments/{pid}/approve", headers=headers("MC1"))
    assert r.status_code == 403

def test_duplicate_checker_approval_is_rejected(client):
    pid = create_and_submit(client, 1500000)
    assert client.post(f"/payments/{pid}/approve", headers=headers("C1")).status_code == 200
    r = client.post(f"/payments/{pid}/approve", headers=headers("C1"))
    assert r.status_code == 409

def test_rejection_requires_reason_and_is_final(client):
    pid = create_and_submit(client)
    r = client.post(f"/payments/{pid}/reject", json={"reason": "Invalid beneficiary"}, headers=headers("C1"))
    assert r.status_code == 200
    assert r.json()["status"] == "REJECTED"
    r = client.post(f"/payments/{pid}/approve", headers=headers("C2"))
    assert r.status_code == 409

def test_daily_limit(client):
    create_and_submit(client, 3000000)
    r = client.post("/payments", json=payload(2500000), headers=headers("M1"))
    pid = r.json()["id"]
    r = client.post(f"/payments/{pid}/submit", headers=headers("M1"))
    assert r.status_code == 409

def test_edit_submitted_returns_to_draft_and_clears_approvals(client):
    pid = create_and_submit(client, 1500000)
    assert client.post(f"/payments/{pid}/approve", headers=headers("C1")).status_code == 200
    r = client.put(f"/payments/{pid}", json=payload(1400000), headers=headers("M1"))
    assert r.status_code == 200
    assert r.json()["status"] == "DRAFT"
    assert r.json()["approvals_received"] == 0

def test_audit_trail_records_actions(client):
    pid = create_and_submit(client)
    client.post(f"/payments/{pid}/approve", headers=headers("C1"))
    r = client.get(f"/payments/{pid}/audit", headers=headers("A1"))
    assert r.status_code == 200
    actions = [item["action"] for item in r.json()]
    assert actions == ["CREATE", "SUBMIT", "APPROVE"]


def test_exact_candidate_pack_sample_scenario(client):
    demo_headers = {"X-User-Id": "M2", "X-Test-Date": "2026-11-16"}
    first = client.post("/payments", json=payload(25000), headers=demo_headers)
    assert first.status_code == 201
    s1 = first.json()["id"]
    assert first.json()["status"] == "DRAFT"

    assert client.post(f"/payments/{s1}/submit", headers=demo_headers).json()["status"] == "SUBMITTED"
    approved = client.post(f"/payments/{s1}/approve", headers=headers("C1"))
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    released = client.post(f"/payments/{s1}/release", headers=headers("A1"))
    assert released.status_code == 200
    assert released.json()["status"] == "RELEASED"

    second = client.post("/payments", json=payload(1500000), headers=demo_headers)
    assert second.status_code == 201
    s2 = second.json()["id"]
    assert client.post(f"/payments/{s2}/submit", headers=demo_headers).json()["status"] == "SUBMITTED"
    first_approval = client.post(f"/payments/{s2}/approve", headers=headers("C1"))
    assert first_approval.status_code == 200
    assert first_approval.json()["status"] == "SUBMITTED"
    assert first_approval.json()["approvals_received"] == 1

    refused = client.post(f"/payments/{s2}/approve", headers=demo_headers)
    assert refused.status_code == 403
    assert refused.json()["detail"] == "Only a Checker can approve or reject"
    unchanged = client.get(f"/payments/{s2}", headers=headers("A1"))
    assert unchanged.json()["status"] == "SUBMITTED"
    assert unchanged.json()["approvals_received"] == 1


def test_ten_lakh_boundary_is_one_approval_and_above_needs_two(client):
    at_boundary = create_and_submit(client, 1_000_000)
    one = client.post(f"/payments/{at_boundary}/approve", headers=headers("C1"))
    assert one.status_code == 200
    assert one.json()["status"] == "APPROVED"

    above_boundary = create_and_submit(client, 1_000_000.01, maker="M2")
    first = client.post(f"/payments/{above_boundary}/approve", headers=headers("C1"))
    assert first.status_code == 200
    assert first.json()["status"] == "SUBMITTED"
    second = client.post(f"/payments/{above_boundary}/approve", headers=headers("C2"))
    assert second.status_code == 200
    assert second.json()["status"] == "APPROVED"


def test_rejected_payment_no_longer_counts_toward_daily_limit(client):
    rejected_id = create_and_submit(client, 3_000_000)
    reject = client.post(
        f"/payments/{rejected_id}/reject",
        json={"reason": "Incorrect beneficiary"},
        headers=headers("C1"),
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "REJECTED"

    next_payment = client.post("/payments", json=payload(3_000_000), headers=headers("M1"))
    assert next_payment.status_code == 201
    submitted = client.post(f"/payments/{next_payment.json()['id']}/submit", headers=headers("M1"))
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"


def test_editing_submitted_payment_removes_it_from_daily_limit(client):
    original_id = create_and_submit(client, 3_000_000)
    edited = client.put(f"/payments/{original_id}", json=payload(3_000_000), headers=headers("M1"))
    assert edited.status_code == 200
    assert edited.json()["status"] == "DRAFT"

    another = client.post("/payments", json=payload(3_000_000), headers=headers("M1"))
    submitted = client.post(f"/payments/{another.json()['id']}/submit", headers=headers("M1"))
    assert submitted.status_code == 200


def test_blank_rejection_reason_and_blank_payment_fields_are_rejected(client):
    pid = create_and_submit(client)
    blank_reason = client.post(
        f"/payments/{pid}/reject", json={"reason": "   "}, headers=headers("C1")
    )
    assert blank_reason.status_code == 422
    assert client.get(f"/payments/{pid}", headers=headers("A1")).json()["status"] == "SUBMITTED"

    invalid = payload()
    invalid["beneficiary_name"] = "   "
    response = client.post("/payments", json=invalid, headers=headers("M2"))
    assert response.status_code == 422


def test_amount_rejects_more_than_two_decimal_places_and_non_finite_values(client):
    for invalid_amount in (10.001, "NaN", "Infinity"):
        response = client.post("/payments", json=payload(invalid_amount), headers=headers("M1"))
        assert response.status_code == 422


def test_amount_above_old_32_bit_paise_ceiling_can_be_created_as_draft(client):
    response = client.post("/payments", json=payload(30_000_000), headers=headers("M1"))
    assert response.status_code == 201
    assert response.json()["amount"] == 30_000_000
    # It is valid to create a draft; the daily submission cap is enforced on submit.
    submit = client.post(f"/payments/{response.json()['id']}/submit", headers=headers("M1"))
    assert submit.status_code == 409
