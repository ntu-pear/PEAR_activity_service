import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

class BaseScript(ABC):
    """
    Abstract base class for messaging scripts
    """
    
    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.start_time = None
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'skipped_count': 0,
            'errors': []
        }
        
        # Set up logging for debugging purposes
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if self.dry_run else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'{self.__class__.__name__}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
        
        # Suppress noisy third-party library logs
        logging.getLogger('pika').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        # Suppress messaging internal logs
        logging.getLogger('messaging.producer_manager').setLevel(logging.WARNING)
        logging.getLogger('messaging.rabbitmq_client').setLevel(logging.WARNING)
        logging.getLogger('messaging').setLevel(logging.WARNING)
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_total_count(self) -> int:
        """Get total number of items to process"""
        pass
    
    @abstractmethod
    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of items to process"""
        pass
    
    @abstractmethod
    def process_item(self, item: Any) -> bool:
        """Process a single item. Return True if successful, False otherwise"""
        pass
    
    def run(self):
        """Main execution method"""
        self.start_time = time.time()
        
        try:
            total_count = self.get_total_count()
            self.logger.info(f"Starting {self.__class__.__name__}")
            self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
            self.logger.info(f"Total items to process: {total_count}")
            self.logger.info(f"Batch size: {self.batch_size}")
            
            if total_count == 0:
                self.logger.warning("No items found to process")
                return
            
            # Process in batches
            offset = 0
            while offset < total_count:
                batch = self.fetch_batch(offset, self.batch_size)
                
                if not batch:
                    self.logger.warning(f"No items found in batch starting at offset {offset}")
                    break
                
                self.logger.info(f"Processing batch {offset // self.batch_size + 1}: "
                               f"items {offset + 1}-{min(offset + len(batch), total_count)} of {total_count}")
                
                # Process each item in the batch
                for item in batch:
                    self.stats['total_processed'] += 1
                    
                    try:
                        success = self.process_item(item)
                        if success:
                            self.stats['success_count'] += 1
                        else:
                            self.stats['skipped_count'] += 1
                    except Exception as e:
                        self.stats['error_count'] += 1
                        error_msg = f"Error processing item {getattr(item, 'id', 'unknown')}: {str(e)}"
                        self.stats['errors'].append(error_msg)
                        self.logger.error(error_msg)
                
                offset += len(batch)
                
                # Progress update every batch
                self._log_progress()
                
                # Small delay to avoid overwhelming the system
                if not self.dry_run:
                    time.sleep(0.1)
        
        except Exception as e:
            self.logger.error(f"Fatal error during execution: {str(e)}")
            raise
        finally:
            self._log_summary()
    
    def _log_progress(self):
        """Log current progress"""
        elapsed = time.time() - self.start_time
        rate = self.stats['total_processed'] / elapsed if elapsed > 0 else 0
        
        self.logger.info(f"Progress: {self.stats['total_processed']} processed "
                        f"({self.stats['success_count']} success, "
                        f"{self.stats['error_count']} errors, "
                        f"{self.stats['skipped_count']} skipped) "
                        f"at {rate:.2f} items/sec")
    
    def _log_summary(self):
        """Log final summary"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self.logger.info("=" * 60)
        self.logger.info(f"{self.__class__.__name__} SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        self.logger.info(f"Total time: {elapsed:.2f} seconds")
        self.logger.info(f"Total processed: {self.stats['total_processed']}")
        self.logger.info(f"Successful: {self.stats['success_count']}")
        self.logger.info(f"Errors: {self.stats['error_count']}")
        self.logger.info(f"Skipped: {self.stats['skipped_count']}")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['success_count'] / self.stats['total_processed']) * 100
            self.logger.info(f"Success rate: {success_rate:.2f}%")
            
            if elapsed > 0:
                rate = self.stats['total_processed'] / elapsed
                self.logger.info(f"Average rate: {rate:.2f} items/sec")
        
        if self.stats['errors']:
            self.logger.error(f"Errors encountered ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                self.logger.error(f"  - {error}")
            if len(self.stats['errors']) > 10:
                self.logger.error(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        self.logger.info("=" * 60)
