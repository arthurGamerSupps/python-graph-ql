import logging
import time
from typing import Dict, Optional
from shopify_graphql import ShopifyGraphQLClient
from config import Config
from exceptions import CodeCreationException

class DiscountCodeRepository:
    """Handles Shopify GraphQL operations for discount codes"""
    
    def __init__(self, client: ShopifyGraphQLClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    def find_by_code(self, code: str) -> Optional[str]:
        """Find discount code by code value, returns ID if exists"""
        query = self._build_find_query(code)
        
        try:
            result = self.client.execute_query(query)
            return self._extract_id_from_find_result(result)
        except Exception as e:
            self.logger.error(f"Exception finding code '{code}': {str(e)}")
            return None
    
    def create(self, code: str, title: Optional[str] = None) -> Optional[str]:
        """Create a new discount code"""
        if not title:
            title = f"{code}"
        
        mutation = self._build_create_mutation(code, title)
        
        try:
            result = self.client.execute_query(mutation)
            return self._handle_creation_result(result, code)
        except Exception as e:
            self.logger.error(f"Exception creating code '{code}': {str(e)}")
            return None
    
    def _build_find_query(self, code: str) -> str:
        """Build GraphQL query to find discount code"""
        return f"""
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
              }}
            }}
          }}
        }}
        """
    
    def _build_create_mutation(self, code: str, title: str) -> str:
        """Build GraphQL mutation to create discount code"""
        config = Config()
        return f"""
        mutation {{
          discountCodeBasicCreate(
            basicCodeDiscount: {{
              title: "{title}"
              code: "{code}"
              startsAt: "{config.DEFAULT_STARTS_AT}"
              customerSelection: {{ all: true }}
              customerGets: {{
                value: {{ percentage: {config.DEFAULT_DISCOUNT_PERCENTAGE} }}
                items: {{ all: true }}
              }}
            }}
          ) {{
            codeDiscountNode {{
              id
              codeDiscount {{
                ... on DiscountCodeBasic {{
                  title
                  codes(first: 1) {{
                    edges {{
                      node {{
                        code
                      }}
                    }}
                  }}
                }}
              }}
            }}
            userErrors {{
              field
              message
            }}
          }}
        }}
        """
    
    def _extract_id_from_find_result(self, result: Dict) -> Optional[str]:
        """Extract discount ID from find query result"""
        if 'errors' in result:
            error_msg = result['errors'][0]['message'] if result['errors'] else 'Unknown error'
            self.logger.warning(f"Error in find result: {error_msg}")
            return None
        
        code_data = result.get('data', {}).get('codeDiscountNodeByCode')
        return code_data.get('id') if code_data else None
    
    def _handle_creation_result(self, result: Dict, code: str) -> Optional[str]:
        """Handle the result of discount creation mutation"""
        # Check for user errors
        user_errors = result.get('data', {}).get('discountCodeBasicCreate', {}).get('userErrors', [])
        if user_errors:
            error_msg = user_errors[0].get('message', 'Unknown error')
            raise CodeCreationException(f"Error creating discount code '{code}': {error_msg}")
        
        # Get the ID of the newly created discount
        discount_node = result.get('data', {}).get('discountCodeBasicCreate', {}).get('codeDiscountNode', {})
        
        if discount_node and discount_node.get('id'):
            return discount_node.get('id')
        
        # If creation succeeded but ID not immediately available, wait and retry
        self.logger.warning(f"Created code '{code}' but couldn't retrieve ID immediately")
        time.sleep(Config.RETRY_DELAY)
        return self.find_by_code(code) 