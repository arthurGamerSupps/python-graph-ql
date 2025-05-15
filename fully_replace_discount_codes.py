#!/usr/bin/env python3
import json
import logging
import os
import random
import string
from tqdm import tqdm
from shopify_graphql import ShopifyGraphQLClient
from load_discount_codes import load_discount_codes_and_ids


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_discount_code(client, code_id="gid://shopify/DiscountCodeNode/1678442529139"):
    """Delete a discount code from Shopify"""
    mutation = f"""
    mutation {{
        discountCodeDelete(id: "{code_id}") {{
            deletedCodeDiscountId
            userErrors {{
                field
                message
            }}
        }}
    }}
    """
    
    try:
        result = client.execute_query(mutation)
        
        # Check for user errors
        user_errors = result.get('data', {}).get('discountCodeDelete', {}).get('userErrors', [])
        if user_errors:
            error_msg = user_errors[0].get('message', 'Unknown error')
            logger.error(f"Error deleting discount code '{code_id}': {error_msg}")
            return False
            
        deleted_id = result.get('data', {}).get('discountCodeDelete', {}).get('deletedCodeDiscountId')
        if deleted_id:
            logger.info(f"Successfully deleted discount code with ID: {deleted_id}")
            return True
        else:
            logger.warning(f"Deletion response received but couldn't confirm deletion of code: {code_id}")
            return False
            
    except Exception as e:
        logger.error(f"Exception deleting discount code '{code_id}': {str(e)}")
        return False

def create_discount_code(client, code):
    """Create a new discount code in Shopify"""
    mutation = f"""
    mutation {{
      discountCodeAppCreate(
        codeAppDiscount: {{
          title: "{code}"
          functionId: "2ac7f32e-3b6b-48b3-a7d3-ea8fba68e876"
          startsAt: "2025-04-30T00:00:00"
          combinesWith: {{
            productDiscounts: true
          }}
          code: "{code}"
          discountClasses: [SHIPPING, ORDER, PRODUCT]
        }}
      ) {{
        codeAppDiscount {{
          discountId
        }}
        userErrors {{
          field
          message
        }}
      }}
    }}
    """
    
    try:
        result = client.execute_query(mutation)
        
        # Check for user errors
        user_errors = result.get('data', {}).get('discountCodeAppCreate', {}).get('userErrors', [])
        if user_errors:
            error_msg = user_errors[0].get('message', 'Unknown error')
            logger.error(f"Error creating discount code '{code}': {error_msg}")
            return None
            
        discount_id = result.get('data', {}).get('discountCodeAppCreate', {}).get('codeAppDiscount', {}).get('discountId')
        if discount_id:
            logger.info(f"Successfully created discount code '{code}' with ID: {discount_id}")
            return discount_id
        else:
            logger.warning(f"Creation response received but couldn't confirm creation of code: {code}")
            return None
            
    except Exception as e:
        logger.error(f"Exception creating discount code '{code}': {str(e)}")
        return None

class ResultsFileManager:
    """Handles file operations for saving results in a JSON file with append functionality"""
    
    def __init__(self, filename_base="replaced_discount_codes"):
        self.filename = self._generate_filename(filename_base)
        self.entry_count = 0
        
        # Initialize with empty JSON object
        with open(self.filename, 'w') as f:
            f.write("{\n}")
        
        logger.info(f"Created results file: {self.filename}")
    
    def _generate_filename(self, base):
        """Generate unique filename with random suffix"""
        suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
        return f"{base}_{suffix}.json"
    
    def save_results(self, results):
        """Save results by appending to the file as JSON-formatted strings"""
        if not results:
            logger.info("No new results to save")
            return
                
        # Count of entries being added in this batch
        batch_count = len(results)
            
        try:
            # Open file in read mode first to check state
            with open(self.filename, 'r') as f:
                content = f.read().strip()
                # Check if file just has empty braces
                is_empty = content == "{}" or content == "{\n}"
            
            # Open in append mode to add entries
            with open(self.filename, 'r+') as f:
                # Find the last occurrence of }
                f.seek(0)
                content = f.read()
                last_brace_pos = content.rfind("}")
                
                if last_brace_pos > 0:
                    # Position right before the closing brace
                    f.seek(last_brace_pos)
                    
                    # If not empty, need a comma
                    prefix = "" if is_empty else ",\n"
                    
                    # Write entries as formatted JSON strings
                    entries = []
                    for code, id_value in results.items():
                        entry = f'  "{code}": "{id_value}"'
                        entries.append(entry)
                    
                    # Combine all entries with commas and write
                    f.seek(last_brace_pos)
                    f.write(prefix + "\n" + ",\n".join(entries) + "\n}")
                else:
                    # Something's wrong with the file
                    logger.warning("File format issue - rewriting entire file")
                    all_results = results.copy()
                    f.seek(0)
                    f.truncate()
                    json.dump(all_results, f, indent=2)
            
            # Update the entry count
            self.entry_count += batch_count
            
            # Log success
            logger.info(f"Saved {batch_count} entries to {self.filename}")
            logger.info(f"Total results saved so far: {self.entry_count}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def process_discount_codes(codes, batch_size=10):
    """Process all discount codes: delete old ones and create new ones"""
    client = ShopifyGraphQLClient(use_partner_auth=True)
    results_manager = ResultsFileManager()
    
    # Process codes in batches to save results periodically
    batch_results = {}
    total_processed = 0
    
    # Get total count of codes for progress bar
    total_codes = len(codes)
    
    # Use tqdm to show progress with the actual number of codes
    for code, code_id in tqdm(codes.items(), desc="Processing discount codes", unit="code", total=total_codes):
        logger.info(f"Processing discount code: {code}")
        
        # Delete the existing code
        success = delete_discount_code(client, code_id)
        if not success:
            logger.warning(f"Failed to delete code {code}, skipping recreation")
            continue
        
        # Create a new code with the same name
        new_id = create_discount_code(client, code)
        if new_id:
            batch_results[code] = new_id
            total_processed += 1
        
        # Save results when batch is full
        if len(batch_results) >= batch_size:
            results_manager.save_results(batch_results)
            batch_results = {}
    
    # Save any remaining results
    if batch_results:
        results_manager.save_results(batch_results)
    
    logger.info(f"Completed processing {total_processed} discount codes")
    return total_processed

if __name__ == "__main__":
    logger.info("Starting discount code replacement process")
    codes = load_discount_codes_and_ids('discount_code_results_bcm.json')
    logger.info(f"Loaded {len(codes)} unique discount codes with IDs")
    
    process_discount_codes(codes)
    
    logger.info("Discount code replacement completed")
    