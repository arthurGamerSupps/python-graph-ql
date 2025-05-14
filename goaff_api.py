import json
import requests
from datetime import datetime
import os
import argparse


def get_affiliates(max_affiliates=5000):
    """
    Fetch all affiliates from the GoAffPro API, handling pagination
    
    Args:
        max_affiliates: Maximum number of affiliates to fetch (safety limit)
    """
    # API endpoint for getting affiliates
    base_url = "https://api.goaffpro.com/v1/admin/affiliates"
    
    # API token for authentication
    token = "57d03ecd24dbfed5c1eea2572c3703397a5321691ed995666eff5003c1a165d1"
    
    # Set up headers with authentication
    headers = {
        "x-goaffpro-access-token": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # All affiliates will be stored here
    all_affiliates = []
    
    # Start with the first page
    page = 1
    more_pages = True
    total_retrieved = 0
    
    try:
        # Fetch all pages of affiliates
        while more_pages and total_retrieved < max_affiliates:
            print(f"Fetching page {page}...")
            
            # Add pagination parameters
            params = {
                "page": page,
                "limit": 100,  # Maximum allowed per page
                "fields": "id,name,email,ref_code,ref_codes,coupon,coupons,company_name,status,created_at,updated_at"  # Required fields parameter
            }
            
            # Make the API request
            response = requests.get(base_url, headers=headers, params=params)
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Extract affiliate data
            affiliates_in_page = data.get("affiliates", [])
            all_affiliates.extend(affiliates_in_page)
            
            # Extract pagination information
            if page == 1:
                total = data.get("total", 0)
                total_pages = data.get("total_pages", 1)
                print(f"Found {total} affiliates across {total_pages} pages")
                
                # Set max_affiliates to the actual total if lower than our limit
                if total and total < max_affiliates:
                    max_affiliates = total
                    print(f"Setting maximum affiliates to fetch to {max_affiliates}")
            
            total_retrieved += len(affiliates_in_page)
            print(f"Page {page}: Retrieved {len(affiliates_in_page)} affiliates (Total: {total_retrieved})")
            
            # Check if we should continue paginating
            # Either we have fewer affiliates than the limit, 
            # or we've reached the total pages reported by the API
            if len(affiliates_in_page) < params["limit"] or (data.get("total_pages") and page >= data.get("total_pages")):
                more_pages = False
            else:
                page += 1
        
        if total_retrieved >= max_affiliates:
            print(f"\nReached maximum affiliate limit of {max_affiliates}")
        
        print(f"\nTotal affiliates retrieved: {len(all_affiliates)}")
        return all_affiliates
    
    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP Error: {http_err}")
        if 'response' in locals():
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as err:
        print(f"\nError: {err}")
    except json.JSONDecodeError:
        print(f"\nError: Could not parse response as JSON")
        if 'response' in locals():
            print(f"Response: {response.text}")
    
    return []


def get_affiliate(affiliate_id):
    """
    Fetch a single affiliate by ID
    
    Args:
        affiliate_id: The ID of the affiliate to fetch
        
    Returns:
        dict: The affiliate data or empty dict if not found
    """
    # API endpoint for getting a single affiliate
    url = f"https://api.goaffpro.com/v1/admin/affiliates/{affiliate_id}"
    
    # API token for authentication
    token = "57d03ecd24dbfed5c1eea2572c3703397a5321691ed995666eff5003c1a165d1"
    
    # Set up headers with authentication
    headers = {
        "x-goaffpro-access-token": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Fields to request
    params = {
        "fields": "id,name,email,ref_code,ref_codes,coupon,coupons,company_name,status,created_at,updated_at"
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        return data.get("affiliate", {})
        
    except requests.exceptions.HTTPError as http_err:
        status_code = response.status_code if 'response' in locals() else 'unknown'
        print(f"\nHTTP Error ({status_code}) fetching affiliate {affiliate_id}: {http_err}")
        if status_code == 404:
            print(f"Affiliate with ID {affiliate_id} not found")
        elif status_code == 401:
            print("Authentication failed - please check your API token")
        elif status_code == 403:
            print("Permission denied - your token may not have the required permissions")
    except requests.exceptions.RequestException as err:
        print(f"\nError fetching affiliate {affiliate_id}: {err}")
    except json.JSONDecodeError:
        print(f"\nError: Could not parse response as JSON for affiliate {affiliate_id}")
    
    return {}


def get_all_affiliates_with_codes(save_to_file=True, max_affiliates=5000):
    """
    Fetch all affiliates with their discount codes
    
    Args:
        save_to_file: If True, save results to a timestamped JSON file
        max_affiliates: Maximum number of affiliates to fetch
    """
    # Get all affiliates (including codes which are already in the response)
    affiliates = get_affiliates(max_affiliates=max_affiliates)
    
    if not affiliates:
        print("No affiliates found.")
        return []
    
    # Display summary information only
    print(f"\nRetrieved {len(affiliates)} affiliates")
    
    # Count different types of codes
    ref_code_count = 0
    coupon_code_count = 0
    
    for affiliate in affiliates:
        # Count ref codes
        ref_codes = affiliate.get('ref_codes', [])
        ref_code_count += len(ref_codes)
        
        # Count coupon codes
        main_coupon = affiliate.get('coupon', {})
        all_coupons = affiliate.get('coupons', [])
        
        if main_coupon and main_coupon.get('code'):
            coupon_code_count += 1
        
        if all_coupons:
            coupon_code_count += len(all_coupons)
    
    print(f"Found {ref_code_count} referral codes and {coupon_code_count} coupon codes")
    
    # Save to file if requested
    if save_to_file and affiliates:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"goaff_affiliates_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({"affiliates": affiliates, "timestamp": timestamp}, f, indent=2)
            print(f"\nSaved results to {os.path.abspath(filename)}")
        except Exception as e:
            print(f"\nError saving to file: {e}")
    
    return affiliates


def extract_all_codes(affiliates, save_to_file=True):
    """
    Extract all unique codes from the affiliates data
    
    Args:
        affiliates: List of affiliate data
        save_to_file: If True, save the codes to a JSON file
        
    Returns:
        list: All unique discount codes
    """
    all_discount_codes = []
    
    # Process each affiliate to gather all codes
    for affiliate in affiliates:
        # Extract referral codes
        ref_codes = affiliate.get('ref_codes', [])
        if ref_codes:
            for code in ref_codes:
                if code and code.strip():  # Only add non-empty codes
                    all_discount_codes.append(code.strip())
        
        # Extract main coupon code
        main_coupon = affiliate.get('coupon', {})
        if main_coupon and main_coupon.get('code'):
            code = main_coupon.get('code')
            if code and code.strip():  # Only add non-empty codes
                all_discount_codes.append(code.strip())
        
        # Extract all other coupon codes
        all_coupons = affiliate.get('coupons', [])
        if all_coupons:
            for coupon in all_coupons:
                if coupon.get('code') and coupon.get('code').strip():
                    all_discount_codes.append(coupon.get('code').strip())
    
    # Get unique codes (case insensitive)
    unique_codes = list(set(code.upper() for code in all_discount_codes))
    
    # Sort the codes alphabetically
    unique_codes.sort()
    
    print(f"\nFound {len(all_discount_codes)} total discount codes")
    print(f"Extracted {len(unique_codes)} unique discount codes (case insensitive)")
    
    # Save to file if requested
    if save_to_file and unique_codes:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"discount_codes_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "discount_codes": unique_codes,
                    "total_codes_found": len(all_discount_codes),
                    "unique_codes_count": len(unique_codes),
                    "timestamp": timestamp
                }, f, indent=2)
            print(f"Saved all discount codes to {os.path.abspath(filename)}")
        except Exception as e:
            print(f"Error saving codes to file: {e}")
    
    return unique_codes


def main():
    """
    Command line interface for the GoAffPro API client
    """
    parser = argparse.ArgumentParser(description="GoAffPro API Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Get all affiliates command
    all_parser = subparsers.add_parser("all", help="Get all affiliates and their codes")
    all_parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    all_parser.add_argument("--extract-codes", action="store_true", help="Extract all unique codes and save to a separate file")
    all_parser.add_argument("--max", type=int, default=3500, help="Maximum number of affiliates to fetch (default: 3500)")
    
    # Get single affiliate command
    single_parser = subparsers.add_parser("affiliate", help="Get a single affiliate by ID")
    single_parser.add_argument("id", help="Affiliate ID")
    
    # Extract codes from existing JSON file
    extract_parser = subparsers.add_parser("extract-codes", help="Extract codes from existing JSON file")
    extract_parser.add_argument("file", help="Path to JSON file with affiliate data")
    
    args = parser.parse_args()
    
    if args.command == "all":
        affiliates = get_all_affiliates_with_codes(save_to_file=not args.no_save, max_affiliates=args.max)
        if args.extract_codes and affiliates:
            extract_all_codes(affiliates)
    elif args.command == "affiliate":
        affiliate = get_affiliate(args.id)
        if affiliate:
            # Display code information
            affiliate_name = affiliate.get('name', 'Unknown')
            affiliate_id = affiliate.get('id')
            
            # Gather coupon information
            ref_codes = affiliate.get('ref_codes', [])
            main_coupon = affiliate.get('coupon', {})
            all_coupons = affiliate.get('coupons', [])
            
            # Print summary of codes
            print(f"\nAffiliate: {affiliate_name} (ID: {affiliate_id})")
            if ref_codes:
                print(f"  Referral codes: {', '.join(ref_codes)}")
            
            coupon_codes = []
            if main_coupon and main_coupon.get('code'):
                coupon_codes.append(main_coupon.get('code'))
            
            if all_coupons:
                for coupon in all_coupons:
                    if coupon.get('code') and coupon.get('code') not in coupon_codes:
                        coupon_codes.append(coupon.get('code'))
            
            if coupon_codes:
                print(f"  Coupon codes: {', '.join(coupon_codes)}")
        else:
            print(f"No affiliate found with ID: {args.id}")
    elif args.command == "extract-codes":
        try:
            with open(args.file, 'r') as f:
                data = json.load(f)
                
            affiliates = data.get("affiliates", [])
            if affiliates:
                extract_all_codes(affiliates)
            else:
                print(f"No affiliates found in file: {args.file}")
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 