from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Coupon:
    id: str
    owner_username: str
    category: str
    brand: str
    offer_amount: str
    expiry_date: str  # Format: YYYY-MM-DD
    code: str = "N/A" # Coupon code
    status: str = "available"  # available, exchanged

    def is_expired(self) -> bool:
        try:
            exp = datetime.strptime(self.expiry_date, "%Y-%m-%d")
            return datetime.now() > exp
        except ValueError:
            return False

    def to_dict(self):
        return {
            "id": self.id,
            "owner_username": self.owner_username,
            "category": self.category,
            "brand": self.brand,
            "offer_amount": self.offer_amount,
            "expiry_date": self.expiry_date,
            "code": self.code,
            "status": self.status
        }

    @staticmethod
    def from_dict(data):
        return Coupon(
            id=data["id"],
            owner_username=data["owner_username"],
            category=data["category"],
            brand=data["brand"],
            offer_amount=data["offer_amount"],
            expiry_date=data["expiry_date"],
            code=data.get("code", "N/A"),
            status=data.get("status", "available")
        )
