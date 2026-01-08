import heapq
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional
from .user import User
from .coupon import Coupon

class DataManager:
    def __init__(self):
        self.users: Dict[str, User] = {}  # HashMap: username -> User
        self.coupons: Dict[str, Coupon] = {}  # HashMap: id -> Coupon
        
        # DSA: Categorization
        self.coupons_by_category: Dict[str, List[str]] = {
            "Food": [],
            "Beauty": [],
            "Electronics": [],
            "Subscriptions": []
        }
        
        # DSA: Min-Heap for Expiry ((expiry_date_obj, coupon_id))
        self.expiry_heap = []
        
        # DSA: Queue for Recent Activity (just strings for display)
        self.recent_activity = deque(maxlen=10)

    def add_user(self, user: User):
        self.users[user.username] = user

    def get_user(self, username: str) -> Optional[User]:
        return self.users.get(username)

    def add_coupon(self, coupon: Coupon):
        self.coupons[coupon.id] = coupon
        
        # Add to Category Map
        if coupon.category in self.coupons_by_category:
            self.coupons_by_category[coupon.category].append(coupon.id)
        
        # Add to Min-Heap
        try:
            exp_date = datetime.strptime(coupon.expiry_date, "%Y-%m-%d")
            heapq.heappush(self.expiry_heap, (exp_date, coupon.id))
        except ValueError:
            pass # Invalid date, maybe handle gracefully or skip heap
            
        self.log_activity(f"User {coupon.owner_username} added a {coupon.brand} coupon.")

    def get_coupons_by_category(self, category: str) -> List[Coupon]:
        self.cleanup_expired()  # Lazy cleanup
        if category not in self.coupons_by_category:
            return []
        
        valid_coupons = []
        for coupon_id in self.coupons_by_category[category]:
            c = self.coupons.get(coupon_id)
            if c and c.status == "available" and not c.is_expired():
                valid_coupons.append(c)
        return valid_coupons

    def cleanup_expired(self):
        """Removes expired coupons using the Min-Heap."""
        now = datetime.now()
        
        # Peek at top of heap
        while self.expiry_heap:
            expiry_date, coupon_id = self.expiry_heap[0]
            if expiry_date < now:
                # Expired
                heapq.heappop(self.expiry_heap)
                # Remove from main dict or mark expired
                if coupon_id in self.coupons:
                    print(f"Removing expired coupon: {coupon_id}")
                    # We can either delete it or mark it. User requirement: "Expired coupons are automatically removed"
                    # Let's fully remove available ones.
                    # But we also need to maintain consistency in category lists...
                    # Implementation detail: It's harder to remove from the category list efficiently (O(N)).
                    # However, we can just remove from the main `coupons` dict, and `get_coupons_by_category` will handle the missing key check.
                    del self.coupons[coupon_id]
            else:
                # Top is not expired, so nothing else is (min-heap property)
                break

    def exchange_coupon(self, taker_username: str, coupon_id: str) -> bool:
        taker = self.get_user(taker_username)
        coupon = self.coupons.get(coupon_id)
        
        if not taker or not coupon:
            return False
            
        if not taker.can_take_coupon():
            return False
            
        if coupon.status != "available":
            return False
            
        if coupon.owner_username == taker_username:
            return False # Cannot take own coupon
            
        # Execute Exchange
        coupon.status = "exchanged"
        taker.coupons_taken += 1
        taker.taken_history.append(coupon.id)
        
        owner = self.get_user(coupon.owner_username)
        if owner:
            # Owner gave this, but we credit them when they ADDED it? 
            # Or is 'coupons_given' incremented when someone takes it?
            # Usually 'Given' means 'Uploaded'. Let's stick to 'Given' = Uploaded.
            pass
            
        self.log_activity(f"User {taker_username} claimed {coupon.brand} coupon from {coupon.owner_username}.")
        return True

    def log_activity(self, message: str):
        self.recent_activity.appendleft(f"[{datetime.now().strftime('%H:%M')}] {message}")

    def get_all_coupons(self):
        return list(self.coupons.values())
        
    def get_soon_to_expire(self, days=3) -> List[Coupon]:
        """Returns coupons expiring fast (but not yet expired) logic using heap could be complex if we just want next few.
        Use sorting or heap nsmallest for simplicity."""
        # Simple implementation: Scan active coupons or use heap nsmallest
        # Only for display on sidebar
        soon = []
        now = datetime.now()
        for c in self.coupons.values():
            if c.status == "available" and not c.is_expired():
                try:
                    exp = datetime.strptime(c.expiry_date, "%Y-%m-%d")
                    delta = (exp - now).days
                    if 0 <= delta <= days:
                        soon.append(c)
                except:
                    pass
        return soon
