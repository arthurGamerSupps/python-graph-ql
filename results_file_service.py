import json
import logging
import random
import string
import os
from typing import Dict
from config import Config
from exceptions import FileOperationException

class ResultsFileService:
    """Handles file operations for saving results"""
    
    def __init__(self, base_filename: str = None):
        self.config = Config()
        self.base_filename = base_filename or self.config.BASE_FILENAME
        self.filename = self._generate_filename()
        self.logger = logging.getLogger(__name__)
        self.entry_count = 0
        
        # Initialize with empty JSON object
        with open(self.filename, 'w') as f:
            f.write("{\n}")
        
        # Log initial file size
        self._log_file_size()
    
    def save_results(self, results: Dict[str, str], is_interim: bool = False):
        """Save results by appending to the file as JSON-formatted strings"""
        try:
            if not results:
                self.logger.info("No new results to save")
                return
                
            # Count of entries being added in this batch
            batch_count = len(results)
            
            # Open file in read mode first to check state
            with open(self.filename, 'r') as f:
                content = f.read().strip()
                # Check if file just has empty braces
                is_empty = content == "{}" or content == "{\n}"
            
            # Open in append mode to add entries
            with open(self.filename, 'r+') as f:
                # Move to position before the closing brace
                f.seek(0, os.SEEK_END)
                position = f.tell()
                
                # Go back to before the closing brace
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
                    self.logger.warning("File format issue - rewriting entire file")
                    all_results = results.copy()
                    f.seek(0)
                    f.truncate()
                    json.dump(all_results, f, indent=2)
            
            # Update the entry count
            self.entry_count += batch_count
            
            # Log success and file size
            self._log_save_status(self.entry_count, batch_count, is_interim)
            self._log_file_size()
            
        except Exception as e:
            raise FileOperationException(f"Error saving results: {e}")
    
    def _generate_filename(self) -> str:
        """Generate unique filename with random suffix"""
        suffix = ''.join(random.choices(string.ascii_lowercase, k=self.config.FILENAME_SUFFIX_LENGTH))
        return f"{self.base_filename}_{suffix}.json"
    
    def _log_save_status(self, total_count: int, batch_count: int, is_interim: bool):
        """Log save operation status"""
        status = "interim" if is_interim else "final"
        self.logger.info(f"Saved {status} results: {batch_count} entries to {self.filename}")
        self.logger.info(f"Total results saved so far: {total_count}")
    
    def _log_file_size(self):
        """Log current file size in bytes and KB"""
        file_size_bytes = os.path.getsize(self.filename)
        file_size_kb = file_size_bytes / 1024.0
        self.logger.info(f"Current file size: {file_size_bytes} bytes ({file_size_kb:.2f} KB)") 