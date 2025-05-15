#!/usr/bin/env python3
import json
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)    

def load_discount_codes(input_file='extra_codes.json'):
    """Load discount codes from JSON file"""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'codes' in data:
            codes = data['codes']
            logger.info(f"Loaded {len(codes)} discount codes from {input_file}")
            return codes
        else:
            if isinstance(data, list):
                logger.info(f"Loaded {len(data)} discount codes from {input_file}")
                return data
            else:
                logger.error(f"Unexpected format in {input_file}, expecting a dict with 'codes' key")
                return []
    except Exception as e:
        logger.error(f"Error loading discount codes: {e}")
        return []

def load_discount_codes_and_ids(input_file='extra_codes.json'):
    """Load discount codes and their IDs from JSON file"""
    try:

        # Regular JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
    
        if isinstance(data, dict):
            # Create a case-insensitive mapping to avoid duplicate IDs
            unique_code_map = {}
            seen_ids = set()
            
            # First pass: collect all codes grouped by lowercase version
            for code, id_value in data.items():
                lowercase_code = code.lower()
                if lowercase_code not in unique_code_map:
                    unique_code_map[lowercase_code] = []
                unique_code_map[lowercase_code].append((code, id_value))
            
            # Second pass: pick one code per lowercase group to avoid ID conflicts
            final_codes = {}
            for lowercase_code, code_entries in unique_code_map.items():
                # Only keep the first code from each case-insensitive group
                code, id_value = code_entries[0]
                final_codes[code] = id_value
                
                # Log if we're skipping variations
                if len(code_entries) > 1:
                    skipped = [entry[0] for entry in code_entries[1:]]
                    logger.warning(f"Skipping case variations of '{code}': {', '.join(skipped)}")
            
            logger.info(f"Loaded {len(data)} discount codes from file, reduced to {len(final_codes)} unique case-insensitive codes")
            return final_codes
        else:
            logger.error(f"Unexpected format in {input_file}, expecting a dictionary mapping codes to IDs")
            return {}
    except Exception as e:
        logger.error(f"Error loading discount codes and IDs: {e}")
        return {}