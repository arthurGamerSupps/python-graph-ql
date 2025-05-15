import logging
import json
import os
from typing import Dict, List, Tuple
from tqdm import tqdm
from config import Config
from discount_code_service import DiscountCodeService
from results_file_service import ResultsFileService
from code_validator import CodeValidator

class DiscountCodeProcessor:
    """Orchestrates the processing of discount codes"""
    
    def __init__(self, 
                 service: DiscountCodeService,
                 file_service: ResultsFileService,
                 batch_size: int = None,
                 save_frequency: int = None):
        self.config = Config()
        self.service = service
        self.file_service = file_service
        self.batch_size = batch_size or self.config.DEFAULT_BATCH_SIZE
        self.save_frequency = save_frequency or self.config.DEFAULT_SAVE_FREQUENCY
        self.logger = logging.getLogger(__name__)
        # Track successful processing count
        self.successful_count = 0
        self.total_processed = 0
    
    def process_codes(self, codes: List[str]) -> Dict[str, str]:
        """Process all discount codes"""
        self._log_start(codes)
        
        # Start fresh - don't need to track all results in memory
        self.successful_count = 0
        self.total_processed = 0
        
        # Keep track of accumulated results for saving
        accumulated_batch_results = {}
        
        total_batches = (len(codes) + self.batch_size - 1) // self.batch_size
        
        with tqdm(total=total_batches, desc="Processing batches") as pbar:
            for batch_num, batch in enumerate(self._get_batches(codes), 1):
                batch_results, batch_success = self._process_batch(batch)
                
                # Add this batch's results to the accumulated batch results
                accumulated_batch_results.update(batch_results)
                
                # Update counters
                self.total_processed += len(batch_results)
                self.successful_count += batch_success
                
                self._log_batch_complete(batch_num, self.total_processed, len(codes), 
                                       batch_success, len(batch_results), self.successful_count)
                
                # Save accumulated results when we reach the save frequency
                if batch_num % self.save_frequency == 0:
                    self.logger.info(f"Saving {len(accumulated_batch_results)} accumulated results at batch {batch_num}")
                    self.file_service.save_results(accumulated_batch_results, is_interim=True)
                    # Clear accumulated results after saving
                    accumulated_batch_results = {}
                
                pbar.update(1)
        
        # Save any remaining accumulated results at the end
        if accumulated_batch_results:
            self.logger.info(f"Saving {len(accumulated_batch_results)} remaining accumulated results")
            self.file_service.save_results(accumulated_batch_results, is_interim=False)
        
        # Read the final results from file for return value and summary
        final_results = self._read_final_results()
        
        self._log_completion(final_results, codes, self.successful_count)
        return final_results
    
    def _process_batch(self, batch: List[str]) -> Tuple[Dict[str, str], int]:
        """Process a single batch of codes"""
        batch_results = {}
        successful_count = 0
        
        for code in batch:
            # Process every code - no skipping
            discount_code = self.service.ensure_code_exists(code)
            
            if discount_code.id:
                batch_results[discount_code.code] = discount_code.id
                successful_count += 1
            else:
                batch_results[discount_code.code] = discount_code.status.value
        
        return batch_results, successful_count
    
    def _get_batches(self, codes: List[str]) -> List[List[str]]:
        """Split codes into batches"""
        for i in range(0, len(codes), self.batch_size):
            yield codes[i:i + self.batch_size]
    
    def _log_start(self, codes: List[str]):
        """Log processing start"""
        self.logger.info(f"Starting to process {len(codes)} discount codes...")
        self.logger.info(f"Batch size: {self.batch_size}, Save frequency: {self.save_frequency}")
        self.logger.info(f"Results will be saved to: {self.file_service.filename}")
    
    def _log_batch_complete(self, batch_num: int, total_processed: int, total_codes: int,
                          batch_success: int, batch_size: int, total_success: int):
        """Log batch completion status"""
        percent_success = (total_success/total_processed)*100 if total_processed > 0 else 0
        self.logger.info(
            f"Batch {batch_num} complete - Processed {total_processed}/{total_codes} codes. "
            f"Batch success: {batch_success}/{batch_size}. "
            f"Overall success: {total_success}/{total_processed} "
            f"({percent_success:.1f}%)."
        )
    
    def _log_completion(self, results: Dict[str, str], codes: List[str], successful_count: int):
        """Log processing completion"""
        self.logger.info(f"Processing complete. Total results: {len(results)}")
        if len(results) > 0:
            self.logger.info(
                f"Success rate: {successful_count}/{len(results)} "
                f"({(successful_count/len(results))*100:.1f}%)"
            )
        
        if len(results) != len(codes):
            self._log_missing_codes(results, codes)
    
    def _log_missing_codes(self, results: Dict[str, str], codes: List[str]):
        """Log any missing codes"""
        result_keys = set(results.keys())
        code_set = set(CodeValidator.clean(c) if CodeValidator.is_valid(c) else str(c) 
                      for c in codes)
        missing = code_set - result_keys
        
        if missing:
            self.logger.warning(f"Missing codes detected: {len(missing)}")
            sample = list(missing)[:5]
            self.logger.warning(f"Sample missing codes: {sample}")
    
    def _read_final_results(self) -> Dict[str, str]:
        """Read the final results from file"""
        try:
            if os.path.exists(self.file_service.filename) and os.path.getsize(self.file_service.filename) > 0:
                with open(self.file_service.filename, 'r') as f:
                    try:
                        return json.load(f)
                    except json.JSONDecodeError:
                        self.logger.error(f"Could not decode JSON from {self.file_service.filename}")
                        return {}
            return {}
        except Exception as e:
            self.logger.error(f"Error reading results file: {e}")
            return {} 