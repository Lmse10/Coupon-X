import pandas as pd
import json
import time
import os

# --- Configuration ---
COUPONS_JSON_PATH = 'data/coupons.json'
USERS_JSON_PATH = 'data/users.json'
EXCEL_OUTPUT_PATH = 'CouponX_Data_Export.xlsx'
UPDATE_INTERVAL_SECONDS = 30 # How often to check for updates

def load_data_from_json(file_path):
    """Loads and returns data from a JSON file."""
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return {}
    with open(file_path, 'r') as f:
        # The data is stored as a dictionary where keys are IDs (UUIDs or usernames)
        return json.load(f)

def write_to_excel(coupons_data, users_data):
    """Writes the loaded data to different sheets in an Excel file."""
    try:
        # 1. Prepare Coupons Data
        # pd.DataFrame.from_dict easily converts your ID-keyed dictionary into a DataFrame
        coupons_df = pd.DataFrame.from_dict(coupons_data, orient='index')

        # 2. Prepare Users Data
        users_df = pd.DataFrame.from_dict(users_data, orient='index')

        # Create a Pandas Excel writer object using the Openpyxl engine
        with pd.ExcelWriter(EXCEL_OUTPUT_PATH, engine='openpyxl') as writer:
            # Write each DataFrame to a separate sheet
            coupons_df.to_excel(writer, sheet_name='Coupons_Data', index=True, index_label='Coupon_ID')
            users_df.to_excel(writer, sheet_name='Users_Data', index=True, index_label='Username')

        print(f"Successfully exported data to {EXCEL_OUTPUT_PATH}")

    except Exception as e:
        print(f"Error writing to Excel: {e}")

def run_live_export():
    print(f"--- Starting Live Excel Exporter (updates every {UPDATE_INTERVAL_SECONDS} seconds) ---")
    
    # Loop indefinitely to keep checking and updating
    while True:
        try:
            coupons = load_data_from_json(COUPONS_JSON_PATH)
            users = load_data_from_json(USERS_JSON_PATH)
            
            write_to_excel(coupons, users)
            
            # Wait for the next update cycle
            time.sleep(UPDATE_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            print("\nExporter stopped by user (Ctrl+C).")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the loop: {e}")
            time.sleep(UPDATE_INTERVAL_SECONDS) # Wait before trying again

if __name__ == "__main__":
    run_live_export()