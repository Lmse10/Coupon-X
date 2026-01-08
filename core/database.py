import json
import os
from .ds_manager import DataManager
from .user import User
from .coupon import Coupon

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
COUPONS_FILE = os.path.join(DATA_DIR, "coupons.json")

def load_data(manager: DataManager):
    # Load Users
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                data = json.load(f)
                for u_data in data:
                    manager.add_user(User.from_dict(u_data))
        except Exception as e:
            print(f"Error loading users: {e}")

    # Load Coupons
    if os.path.exists(COUPONS_FILE):
        try:
            with open(COUPONS_FILE, 'r') as f:
                data = json.load(f)
                for c_data in data:
                    manager.add_coupon(Coupon.from_dict(c_data))
        except Exception as e:
            print(f"Error loading coupons: {e}")

def save_data(manager: DataManager):
    # Ensure dir exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Save Users
    with open(USERS_FILE, 'w') as f:
        users_list = [u.to_dict() for u in manager.users.values()]
        json.dump(users_list, f, indent=4)

    # Save Coupons
    with open(COUPONS_FILE, 'w') as f:
        # Save all coupons (even exchanged ones, maybe filter expired if we want to clean file)
        coupons_list = [c.to_dict() for c in manager.coupons.values()]
        json.dump(coupons_list, f, indent=4)
