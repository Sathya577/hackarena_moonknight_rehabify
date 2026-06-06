import requests

data = {
    "recovery_area": "Shoulder",
    "pain_score": 7,
    "duration": "6-12 weeks",
    "goal": "Return To Sports"
}

response = requests.post(
    "http://127.0.0.1:8000/generate-profile",
    json=data
)

print(response.json())