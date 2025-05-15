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
    coupons = affiliate.get('coupons', [])
    ref_code = affiliate.get('ref_code')

    # Only add coupon code if it exists
    all_codes_for_affiliate = []
    if coupons:
        if len(coupons) < 2:
            print(f"Less than 2 coupons for affiliate: {affiliate}")
        else:
            for coupon in coupons:
                coupon_code = coupon.get('code')
                if coupon_code != ref_code:
                    all_codes_for_affiliate.append(coupon_code)
    print(f"All extra coupon codes for affiliate: {all_codes_for_affiliate}")
    all_codes.extend(all_codes_for_affiliate)

# Dump all codes as JSON array
with open(f'extra_codes.json', 'w') as f:
    json.dump(all_codes, f, indent=2)



