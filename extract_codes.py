import json
import time
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_codes(file_path='goaff_affiliates_20250514_162308.json'):
    logger.info(f"Reading affiliate data from {file_path}")
    with open(file_path, 'r') as file:
        data = json.load(file)

    codes = []
    logger.info("Processing affiliates...")
    for affiliate in tqdm(data['affiliates'], desc="Processing affiliates"):
        logger.debug(f"Processing affiliate: {affiliate['name']}")
        unique_codes = set()
        if 'ref_codes' in affiliate:
            for code in affiliate['ref_codes']:
                unique_codes.add(code)
        if 'ref_code' in affiliate:
            unique_codes.add(affiliate['ref_code'])

        codes.extend(unique_codes)

    logger.info(f"Found {len(codes)} unique codes")
    return codes


if __name__ == "__main__":
    codes = extract_codes()
    logger.info("Extracted codes:")
    logger.info(codes)
    
    output_file = 'discount_codes.json'
    with open(output_file, 'w') as f:
        json.dump({"codes": codes}, f, indent=2)
    logger.info(f"Saved codes to {output_file}")
