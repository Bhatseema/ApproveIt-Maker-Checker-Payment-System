# ApproveIt – AI Usage Note

## 1. AI Tool Used

**Tool:** ChatGPT (OpenAI)

ChatGPT was used as a development assistant during the implementation, debugging, testing and documentation of the ApproveIt project.

AI suggestions were reviewed and applied based on the project requirements. Code changes were tested locally before considering them complete.

## 2. How AI Was Used

### 2.1 Understanding Requirements and Planning

- Used ChatGPT to understand the Maker-Checker payment approval workflow.
- Reviewed the payment lifecycle, user roles and approval conditions from the assignment.
- Converted the requirements into implementation tasks and test scenarios.
- Discussed design decisions for payment validation, approval thresholds, daily limits and audit logging.

### 2.2 Backend Development and Improvements

ChatGPT assisted with reviewing and improving backend implementation, including:

- FastAPI endpoint and service-layer logic.
- Maker, Checker, Maker-Checker and Admin role permissions.
- Payment creation, editing, submission, approval, rejection and release.
- Prevention of maker self-approval.
- Prevention of duplicate checker approvals.
- Approval threshold logic for payments up to and above INR 10,00,000.
- Daily submission limit of INR 50,00,000 per Maker using the IST calendar date.
- Resetting approval decisions when a submitted payment is edited.
- Payment amount validation and decimal precision.
- Audit trail generation and database transaction handling.
- Concurrent approval safety using SQLite transactions.

### 2.3 Frontend Development

ChatGPT assisted with improving the payment dashboard and role-aware user interface.

Changes included:

- Displaying the payment creator through the **Created By** column.
- Showing actions according to the selected user's role and payment ownership.
- Showing Edit and Submit options only for eligible Maker-owned payments.
- Preventing Makers from approving or rejecting their own payments.
- Showing Approve and Reject options to eligible Checkers.
- Showing Release only to Admin users for approved payments.
- Adding frontend checks to prevent invalid actions before sending requests.

Backend authorization remains responsible for enforcing permissions; frontend visibility is not treated as a security control.

### 2.4 Testing and Debugging

ChatGPT helped identify test commands, understand errors and verify expected results.

The following testing activities were performed:

- Payment lifecycle and validation tests.
- Approval threshold tests.
- Maker self-approval and duplicate approval tests.
- Rejection and daily limit tests.
- Audit trail tests.
- Concurrent approval testing using multiple requests.
- Troubleshooting pytest collection and server connection errors.

The developer executed the tests locally and reviewed the actual responses.

### 2.5 Documentation

ChatGPT assisted in preparing:

- System architecture documentation.
- Database entity relationship diagram.
- Payment lifecycle diagram.
- Design decisions and assumptions.
- Testing and reliability documentation.
- This AI usage note.

## 3. Example of AI-Assisted Problem Solving

**Problem:** The frontend initially displayed similar actions without fully considering the selected user's role and payment ownership.

**AI assistance:** ChatGPT helped identify the required role-aware conditions and suggested frontend checks for Maker, Checker, Maker-Checker and Admin users.

**Implementation:** The frontend was updated to display appropriate actions based on user role, payment ownership and payment status. The Created By column was also added.

**Verification:** The updated dashboard was manually checked using different user roles.

## 4. One AI Mistake Identified and Corrected

During automated testing, an incorrect test filename was initially suggested:

`tests/test_payment.py`

However, the actual project filename was:

`tests/test_payments.py`

The mismatch was identified by inspecting the project's test directory. The command was corrected, and the correct test file executed successfully with 15 passing tests.

This reinforced the importance of checking actual project files instead of assuming filenames.

## 5. Developer's Contribution and Verification

AI was used as an assistant, not as a replacement for development and testing.

The developer:

- Reviewed the original assignment requirements.
- Maintained and worked on the project code.
- Applied and reviewed suggested code changes.
- Ran the application locally.
- Executed Swagger API requests and frontend checks.
- Ran automated tests and examined their results.
- Identified issues and provided additional project context for corrections.
- Reviewed the final implementation and documentation.

## 6. Testing Results at the Time of Documentation

- **15 automated payment tests:** Passed.
- **Separate concurrent approval scenario:** Executed successfully.
- **Swagger API documentation:** Verified through `/docs`.
- **Frontend role-aware actions:** Implemented and manually checked.
- **Full pytest suite:** Further cleanup required because the concurrent test script makes HTTP requests during test collection.

## 7. Conclusion

ChatGPT helped accelerate requirement analysis, backend improvements, frontend development, debugging, testing guidance and documentation.

All reported test results are based on actual local execution. The final implementation and verification remain the developer's responsibility.