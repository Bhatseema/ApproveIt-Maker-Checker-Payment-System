
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8000/payments/49/approve"

def approve(user_id):
    response = requests.post(
        URL,
        headers={"X-User-Id": user_id}
    )
    return user_id, response.status_code, response.text

with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(approve, ["C1", "C2"]))

for result in results:
    print(result)

# Check final payment status
response = requests.get(
    "http://127.0.0.1:8000/payments/49",
    headers={"X-User-Id": "A1"}
)

print("\nFinal payment:")
print(response.status_code)
print(response.json())
