import json
from shopify_graphql import ShopifyGraphQLClient

def run_orca_discount_mutation(title="ORCA1010", code="ORCA1010"):
    # Create the GraphQL client, preferring partner authentication if available
    try:
        client = ShopifyGraphQLClient(use_partner_auth=True)
    except Exception as e:
        print(f"Partner app authentication failed: {e}")
        print("Falling back to admin token authentication...")
        client = ShopifyGraphQLClient(use_partner_auth=False)
    
    # Define the mutation
    mutation = """
    mutation BulkCreatePartnerDiscountCodes_0814 {
      code1_create: discountCodeAppCreate(
        codeAppDiscount: {
          title: "ORCA1010"
          functionId: "2ac7f32e-3b6b-48b3-a7d3-ea8fba68e876"
          startsAt: "2025-04-30T00:00:00"
          combinesWith: {
            productDiscounts: true
          }
          code: "ORCA1010"
          discountClasses: [SHIPPING, ORDER, PRODUCT]
        }
      ) {
        codeAppDiscount {
          discountId
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    
    # Execute the mutation
    print("\nExecuting discount code creation mutation...")
    try:
        result = client.execute_query(mutation)
        # Pretty print the result
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        # Check for user errors
        if result.get('data', {}).get('code1_create', {}).get('userErrors'):
            print("\nEncountered errors:")
            for error in result['data']['code1_create']['userErrors']:
                print(f"- Field: {error.get('field', 'N/A')}, Message: {error.get('message', 'N/A')}")
        else:
            # Success - show the discount ID
            discount_id = result.get('data', {}).get('code1_create', {}).get('codeAppDiscount', {}).get('discountId')
            if discount_id:
                print(f"\nSuccess! Created discount code with ID: {discount_id}")
    except Exception as e:
        print(f"\nError executing mutation: {e}")

if __name__ == "__main__":
    run_orca_discount_mutation() 