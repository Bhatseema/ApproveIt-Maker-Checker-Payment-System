# My Testing Notes

## 1. Open These Links

- UI: http://127.0.0.1:8000/ui/
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 2. Start Backend

Open VS Code terminal:

```powershell
cd C:\Users\LENOVO\Desktop\intership\ApproveIt_Project\ApproveIt
```

Activate environment:

```powershell
..\venv\Scripts\Activate.ps1
```

Run backend:

```powershell
python -m uvicorn app.main:app --reload
```

## 3. Testing Commands

Open another terminal.

Activate environment:

```powershell
..\venv\Scripts\Activate.ps1
```

Run all tests:

```powershell
python -m pytest tests/ -v
```

Run concurrency test:

```powershell
python -m tests.concurrent_test
```

## 4. Manual Testing – Select Users

### Maker Testing

**M1**
1. Select M1.
2. Create a payment.
3. Save it.
4. Check payment ID and Created By.
5. Submit payment.

**M2**
1. Switch to M2.
2. Create another payment.
3. Check whether Created By shows M2.
4. Check whether M1 and M2 payments are correctly separated.
5. Try submitting M1's draft payment. It should be denied.

### Checker Testing

**C1**
1. Select C1.
2. Open pending payments.
3. Approve a payment.
4. Check approval count.

**C2**
1. Select C2.
2. Open the same payment.
3. Approve it.
4. Check whether the second approval is recorded.

### Admin Testing

**A1**
1. Select A1.
2. Open Admin Dashboard.
3. Check payment information.
4. Check audit history.

## 5. Important Scenarios to Test

| Test | What should happen? |
|---|---|
| M1 creates payment | DRAFT |
| M1 submits payment | PENDING |
| M1 approves own payment | Not allowed |
| M2 submits M1's draft | Not allowed |
| ₹5 lakh payment + C1 | One approval |
| ₹15 lakh + C1 | 1/2 approvals |
| ₹15 lakh + C1 again | Duplicate denied |
| ₹15 lakh + C2 | 2/2 approvals |
| Reject payment | REJECTED |
| Release approved payment | RELEASED |
| Exceed ₹50 lakh daily limit | Submission denied |

## 6. Concurrency Testing

First start the backend in Terminal 1.

Then run in Terminal 2:

```powershell
python -m tests.concurrent_test
```

Check:
- C1 and C2 requests execute together.
- Both responses are successful in the expected test.
- Approval count is exactly 2.
- No duplicate approvals.
- Final status is APPROVED.

## 7. Swagger Testing

1. Open `/docs`.
2. Expand an API.
3. Click Try it out.
4. Enter request details.
5. Add `X-User-Id` header.
6. Execute.
7. Check response code and response body.

Example user headers:

```text
X-User-Id: M1
X-User-Id: M2
X-User-Id: C1
X-User-Id: C2
X-User-Id: A1
```

Use only one user ID per request.

## 8. Before Finishing

- Check UI.
- Check Swagger.
- Check M1 and M2.
- Check C1 and C2.
- Check approval rules.
- Check daily limit.
- Check rejection and release.
- Check audit history.
- Run pytest.
- Run concurrency test.