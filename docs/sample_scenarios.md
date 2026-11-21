# ApproveIt sample scenarios

These show the format of the scenarios you will run live in the session, using any tool you like (curl, Postman, your own UI). Payment labels such as S1 are names for this script; your service can use its own IDs. Users are in users.json. Run the steps in order; a 'Refused' result should leave the data unchanged and return a clear error.

| Step | Date | Scenario | Expected result | State after |
| --- | --- | --- | --- | --- |
| 1 | 2026-11-16 | M2 creates payment S1 for ₹25,000.00 (office supplies) | Allowed: Created | DRAFT |
| 2 | 2026-11-16 | M2 submits S1 | Allowed: Submitted | SUBMITTED |
| 3 | 2026-11-16 | C1 approves S1 | Allowed: Approval 1 of 1 | APPROVED |
| 4 | 2026-11-16 | A1 releases S1 | Allowed: Released | RELEASED |
| 5 | 2026-11-16 | M2 creates payment S2 for ₹15,00,000.00 (equipment lease) | Allowed: Created | DRAFT |
| 6 | 2026-11-16 | M2 submits S2 | Allowed: Submitted | SUBMITTED |
| 7 | 2026-11-16 | C1 approves S2 | Allowed: Approval 1 of 2 | SUBMITTED |
| 8 | 2026-11-16 | M2 approves S2 | Refused: Only a Checker can approve or reject | SUBMITTED |
