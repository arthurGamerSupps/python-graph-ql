import logging
from typing import Dict

class ProcessingSummaryReporter:
    """Generates processing summary reports"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def generate_summary(self, results: Dict[str, str], total_codes: int):
        """Generate and log processing summary"""
        total_processed = len(results)
        valid_ids = sum(1 for id_value in results.values() 
                       if not str(id_value).startswith('NO_ID'))
        
        self.logger.info("=" * 50)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total codes provided: {total_codes}")
        self.logger.info(f"Total codes processed: {total_processed}")
        self.logger.info(f"Codes with valid IDs: {valid_ids}")
        
        if total_processed > 0:
            self.logger.info(f"Success rate: {(valid_ids/total_processed)*100:.1f}%")
        
        # Breakdown by status
        status_counts = self._count_by_status(results)
        self.logger.info("Status breakdown:")
        for status, count in status_counts.items():
            self.logger.info(f"  {status}: {count}")
        self.logger.info("=" * 50)
    
    def _count_by_status(self, results: Dict[str, str]) -> Dict[str, int]:
        """Count results by status"""
        status_counts = {}
        
        for id_value in results.values():
            if str(id_value).startswith('NO_ID'):
                status = id_value
            else:
                status = 'VALID_ID'
            
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts 