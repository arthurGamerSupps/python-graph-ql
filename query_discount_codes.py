#!/usr/bin/env python3
import json
import logging
from shopify_graphql import ShopifyGraphQLClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def query_discount_codes():
    """
    Query Shopify for discount codes and return a dictionary with code details
    """
    # Create the GraphQL client, preferring partner authentication if available
    try:
        client = ShopifyGraphQLClient(use_partner_auth=True)
        logger.info("Using partner authentication")
    except Exception as e:
        logger.warning(f"Partner app authentication failed: {e}")
        logger.info("Falling back to admin token authentication...")
        client = ShopifyGraphQLClient(use_partner_auth=False)
    
    # Define the GraphQL query to fetch discount codes
    query = """
    {
      codeDiscountNodes(first: 100) {
        edges {
          node {
            id
            codeDiscount {
              ... on DiscountCodeBasic {
                title
                status
                codes(first: 10) {
                  edges {
                    node {
                      code
                    }
                  }
                }
                customerSelection {
                  all
                }
                customerGets {
                  value {
                    ... on PercentageValue {
                      percentage
                    }
                    ... on FixedAmountValue {
                      amount {
                        amount
                        currencyCode
                      }
                    }
                  }
                }
                startsAt
                endsAt
              }
              ... on DiscountCodeApp {
                title
                status
                codes(first: 10) {
                  edges {
                    node {
                      code
                    }
                  }
                }
                appDiscountType {
                  functionId
                  title
                }
                startsAt
                endsAt
              }
            }
          }
        }
      }
    }
    """
    
    # Execute the query
    logger.info("Executing discount code query...")
    try:
        result = client.execute_query(query)
        
        # Process the results into a dictionary
        discount_codes = {}
        edges = result.get('data', {}).get('codeDiscountNodes', {}).get('edges', [])
        
        for edge in edges:
            node = edge.get('node', {})
            discount_id = node.get('id')
            code_discount = node.get('codeDiscount', {})
            
            # Extract code details based on discount type
            if 'codes' in code_discount:
                code_edges = code_discount.get('codes', {}).get('edges', [])
                for code_edge in code_edges:
                    code = code_edge.get('node', {}).get('code')
                    if code:
                        # Create entry in dictionary for this code
                        discount_codes[code] = {
                            'id': discount_id,
                            'title': code_discount.get('title'),
                            'status': code_discount.get('status'),
                            'starts_at': code_discount.get('startsAt'),
                            'ends_at': code_discount.get('endsAt')
                        }
                        
                        # Add type-specific data
                        if 'appDiscountType' in code_discount:
                            discount_codes[code]['type'] = 'app'
                            discount_codes[code]['function_id'] = code_discount.get('appDiscountType', {}).get('functionId')
                            discount_codes[code]['function_title'] = code_discount.get('appDiscountType', {}).get('title')
                        else:
                            discount_codes[code]['type'] = 'basic'
                            
                            # Extract percentage or fixed amount
                            customer_gets = code_discount.get('customerGets', {})
                            value = customer_gets.get('value', {})
                            
                            if 'percentage' in value:
                                discount_codes[code]['value_type'] = 'percentage'
                                discount_codes[code]['value'] = value.get('percentage')
                            elif 'amount' in value:
                                discount_codes[code]['value_type'] = 'fixed_amount'
                                amount = value.get('amount', {})
                                discount_codes[code]['value'] = amount.get('amount')
                                discount_codes[code]['currency'] = amount.get('currencyCode')
        
        logger.info(f"Found {len(discount_codes)} discount codes")
        return discount_codes
                
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {}

def save_discount_codes(discount_codes, output_file='shopify_discount_codes.json'):
    """
    Save the discount codes dictionary to a JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(discount_codes, f, indent=2)
    logger.info(f"Saved discount codes to {output_file}")

if __name__ == "__main__":
    # Query discount codes
    discount_codes = query_discount_codes()
    
    # Save to file
    if discount_codes:
        save_discount_codes(discount_codes)
    else:
        logger.warning("No discount codes were found or an error occurred") 