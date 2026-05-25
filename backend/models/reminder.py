from pydantic import BaseModel


class ReminderSettings(BaseModel):
    user_id: str
    phone_number: str
    cutoff_hour: int = 21
    enabled: bool = True
