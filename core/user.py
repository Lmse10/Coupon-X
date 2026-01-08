from dataclasses import dataclass, field
from typing import List

@dataclass
class User:
    username: str
    password: str
    is_admin: bool = False
    coupons_given: int = 0
    coupons_taken: int = 0
    # We can store IDs of coupons history
    given_history: List[str] = field(default_factory=list)
    taken_history: List[str] = field(default_factory=list)

    def can_take_coupon(self) -> bool:
        # Rule: 1:1 exchange. Coupons taken <= Coupons given
        # OR "Users can claim coupons only if they have already given the same number of coupons"
        # This usually means you must Give X to Take X.
        # Strict interpretation: current_taken < current_given
        # OR simpler: balance check.
        # Let's assume: You can take if taken_count < given_count.
        return self.coupons_taken < self.coupons_given

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "is_admin": self.is_admin,
            "coupons_given": self.coupons_given,
            "coupons_taken": self.coupons_taken,
            "given_history": self.given_history,
            "taken_history": self.taken_history
        }

    @staticmethod
    def from_dict(data):
        return User(
            username=data["username"],
            password=data["password"],
            is_admin=data.get("is_admin", False),
            coupons_given=data.get("coupons_given", 0),
            coupons_taken=data.get("coupons_taken", 0),
            given_history=data.get("given_history", []),
            taken_history=data.get("taken_history", [])
        )
