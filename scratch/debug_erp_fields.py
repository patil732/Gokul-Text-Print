from services.frappe_client import FrappeClient
import json

def debug_fields():
    client = FrappeClient()
    print("Checking Sales Order fields...")
    sales = client.fetch_data("Sales Order", max_records=1)
    if not sales.empty:
        print("Sales Order columns:", list(sales.columns))
    else:
        print("No Sales Order data found.")

    print("\nChecking Bin fields...")
    bins = client.fetch_data("Bin", max_records=1)
    if not bins.empty:
        print("Bin columns:", list(bins.columns))
    else:
        print("No Bin data found.")

if __name__ == "__main__":
    debug_fields()
