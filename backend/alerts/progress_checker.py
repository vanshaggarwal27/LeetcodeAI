from alerts.elevenlabs_service import generate_message


def check_unsolved_users():
    users = [
        {
            "name": "Bhavya",
            "phone": "+911234567890",
            "solved_today": False
        }
    ]

    for user in users:
        if not user["solved_today"]:
            message = generate_message(user["name"])

            print("Triggering alert for:", user["name"])
            print(message)
