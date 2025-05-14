#!/usr/bin/env python3
import json
import logging
import time
from shopify_graphql import ShopifyGraphQLClient
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_discount_codes(input_file='discount_codes.json'):
    """Load discount codes from JSON file"""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'codes' in data:
            codes = data['codes']
            logger.info(f"Loaded {len(codes)} discount codes from {input_file}")
            return codes
        else:
            logger.error(f"Unexpected format in {input_file}, expecting a dict with 'codes' key")
            return []
    except Exception as e:
        logger.error(f"Error loading discount codes: {e}")
        return []

def find_discount_code_ids(codes, batch_size=5, delay=1.0):
    """
    Query Shopify API to find the ID for each discount code
    Using the codeDiscountNodeByCode query endpoint
    
    Parameters:
    codes (list): List of discount code strings
    batch_size (int): Number of codes to process per batch to avoid rate limits
    delay (float): Delay in seconds between batches to avoid rate limits
    
    Returns:
    dict: Dictionary mapping codes to their IDs and details
    """
    # Initialize results dictionary
    results = {}
    
    # Create GraphQL client
    try:
        client = ShopifyGraphQLClient(use_partner_auth=True)
        logger.info("Using partner authentication")
    except Exception as e:
        logger.warning(f"Partner app authentication failed: {e}")
        logger.info("Falling back to admin token authentication...")
        client = ShopifyGraphQLClient(use_partner_auth=False)
    
    # Process codes in batches with a progress bar
    for i in tqdm(range(0, len(codes), batch_size), desc="Processing code batches"):
        batch = codes[i:i+batch_size]
        
        for code in batch:
            try:
                logger.info(f"Looking up discount code: {code}")
                # Construct query for this code
                query = f"""
                {{
                  codeDiscountNodeByCode(code: "{code}") {{
                    id
                    codeDiscount {{
                      ... on DiscountCodeBasic {{
                        title
                        status
                      }}
                      ... on DiscountCodeApp {{
                        title
                        status
                        appDiscountType {{
                          functionId
                          title
                        }}
                      }}
                    }}
                  }}
                }}
                """
                
                result = client.execute_query(query)
                
                if 'errors' in result:
                    error_message = result['errors'][0]['message'] if result['errors'] else "Unknown error"
                    logger.warning(f"Error querying code '{code}': {error_message}")
                    results[code] = {"error": error_message}
                else:
                    code_data = result.get('data', {}).get('codeDiscountNodeByCode', None)
                    
                    if code_data:
                        results[code] = {
                            "id": code_data.get('id'),
                            "title": code_data.get('codeDiscount', {}).get('title'),
                            "status": code_data.get('codeDiscount', {}).get('status'),
                        }
                        logger.info(f"Found ID for code '{code}': {code_data.get('id')}")
                        
                        # Add app-specific details if available
                        if 'appDiscountType' in code_data.get('codeDiscount', {}):
                            app_type = code_data['codeDiscount']['appDiscountType']
                            results[code]['function_id'] = app_type.get('functionId')
                            results[code]['function_title'] = app_type.get('title')
                            logger.info(f"Code '{code}' is an app discount with function: {app_type.get('title')}")
                    else:
                        # Code not found
                        results[code] = {"exists": False}
                        logger.info(f"No discount found for code: {code}")
            
            except Exception as e:
                logger.error(f"Exception processing code '{code}': {str(e)}")
                results[code] = {"error": str(e)}
        
        # Add delay between batches to avoid rate limits
        if i + batch_size < len(codes):
            time.sleep(delay)
    
    return results

def save_results(results, output_file='discount_code_ids.json'):
    """Save results to a JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results for {len(results)} codes to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

if __name__ == "__main__":
    # Load discount codes
    codes = load_discount_codes()
    
    if not codes:
        logger.error("No discount codes loaded. Exiting.")
        exit(1)
    
    # Find IDs for discount codes
    results = find_discount_code_ids(codes)
    
    # Save results
    save_results(results)
    
    # Print summary
    found = sum(1 for code, data in results.items() if 'id' in data)
    not_found = sum(1 for code, data in results.items() if data.get('exists') is False)
    errors = sum(1 for code, data in results.items() if 'error' in data)
    
    logger.info(f"Summary: {found} codes found, {not_found} codes not found, {errors} errors")