import json
import time
from datetime import datetime

with open('goaff_affiliates_20250515_113523.json', 'r') as f:
    data = json.load(f)

# The data is already a dictionary with 'affiliates' key
affiliates = data['affiliates']
all_codes = []
for affiliate in affiliates:
    # Get ref codes (default to empty list if None)
    ref_codes = affiliate.get('ref_codes', [])
    coupon_codes = affiliate.get('coupon_codes', [])
    # Safely get coupon code if it exists
    coupon = affiliate.get('coupon', {})
    coupon_code = coupon.get('code') if coupon else None
    print(f"Affiliate ID: {affiliate['id']}")
    print(f"Ref Codes: {ref_codes}")
    print(f"Coupon Code: {coupon_code}")
    print(f"Coupon Codes: {coupon_codes}")
    print(f"Coupon: {coupon}")
    time.sleep(10)
    # Only add coupon code if it exists
    all_codes_for_affiliate = ref_codes
    if coupon_code:
        all_codes_for_affiliate.append(coupon_code)
    
    all_codes.extend(all_codes_for_affiliate)

# Dump all codes as JSON array
with open(f'all_codes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
    json.dump(all_codes, f, indent=2)



