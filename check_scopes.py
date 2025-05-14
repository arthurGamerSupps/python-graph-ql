import json
from shopify_graphql import ShopifyGraphQLClient

def check_api_scopes():
    print("Checking API scopes...")
    try:
        client = ShopifyGraphQLClient(use_partner_auth=True)
    except Exception as e:
        print(f"Partner app authentication failed: {e}")
        print("Falling back to admin token authentication...")
        client = ShopifyGraphQLClient(use_partner_auth=False)
    
    # Query to check access scopes
    query = """
    {
      currentAppInstallation {
        accessScopes {
          handle
        }
      }
    }
    """
    
    try:
        result = client.execute_query(query)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        # Extract and list scopes
        if "data" in result and "currentAppInstallation" in result["data"] and "accessScopes" in result["data"]["currentAppInstallation"]:
            scopes = result["data"]["currentAppInstallation"]["accessScopes"]
            print("\nCurrent access scopes:")
            for scope in scopes:
                print(f"- {scope.get('handle')}")
                
            # Check if write_discounts is present
            has_write_discounts = any(scope.get('handle') == 'write_discounts' for scope in scopes)
            if has_write_discounts:
                print("\n✅ The token has the 'write_discounts' scope.")
            else:
                print("\n❌ The token DOES NOT have the 'write_discounts' scope.")
        else:
            print("\nCould not retrieve scopes. Check the API response.")
    except Exception as e:
        print(f"\nError checking API scopes: {e}")

if __name__ == "__main__":
    check_api_scopes() 