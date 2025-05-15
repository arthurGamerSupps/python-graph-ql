import logging
from shopify_graphql import ShopifyGraphQLClient

class ShopifyClientFactory:
    """Factory for creating Shopify clients"""
    
    @staticmethod
    def create_client() -> ShopifyGraphQLClient:
        """Create Shopify GraphQL client with fallback authentication"""
        logger = logging.getLogger(__name__)
        
        try:
            client = ShopifyGraphQLClient(use_partner_auth=True)
            logger.info("Using partner authentication")
            return client
        except Exception as e:
            logger.warning(f"Partner authentication failed: {e}")
            logger.info("Falling back to admin token authentication")
            return ShopifyGraphQLClient(use_partner_auth=False) 