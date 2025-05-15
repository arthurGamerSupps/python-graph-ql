#!/usr/bin/env python3
"""
Shopify Discount Code Manager - Fixed version
A clean, modular implementation for managing discount codes in Shopify
Fixed to properly accumulate all results with efficient file appending
"""

import logging
from config import Config
from code_status import CodeStatus
from discount_code import DiscountCode
from discount_code_repository import DiscountCodeRepository
from discount_code_service import DiscountCodeService
from results_file_service import ResultsFileService
from discount_code_processor import DiscountCodeProcessor
from shopify_client_factory import ShopifyClientFactory
from processing_summary_reporter import ProcessingSummaryReporter
from load_discount_codes import load_discount_codes


def setup_logging() -> logging.Logger:
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def main():
    """Main application entry point"""
    # Setup
    logger = setup_logging()
    logger.info("Starting Shopify Discount Code Manager")
    
    # Load codes
    codes = load_discount_codes()
    if not codes:
        logger.error("No discount codes loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(codes)} discount codes")
    
    # Initialize components
    client = ShopifyClientFactory.create_client()
    repository = DiscountCodeRepository(client)
    service = DiscountCodeService(repository)
    file_service = ResultsFileService()
    processor = DiscountCodeProcessor(service, file_service)
    
    # Process codes - results are saved incrementally to disk
    results = processor.process_codes(codes)
    
    logger.info(f"Results saved to: {file_service.filename}")
    
    # Generate summary
    reporter = ProcessingSummaryReporter(logger)
    reporter.generate_summary(results, len(codes))


if __name__ == "__main__":
    main()