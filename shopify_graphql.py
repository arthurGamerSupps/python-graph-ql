import os
import json
import requests
import webbrowser
import http.server
import socketserver
import threading
import time
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ShopifyGraphQLClient:
    def __init__(self, use_partner_auth=False):
        # Store domain
        self.shop_domain = "gamersupps.myshopify.com"  # Update with your shop domain
        
        if use_partner_auth:
            # Use OAuth flow for partner app
            self.client_id = os.getenv('SHOPIFY_CLIENT_ID')
            self.client_secret = os.getenv('SHOPIFY_CLIENT_SECRET')
            self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
            
            if not self.client_id or not self.client_secret:
                raise ValueError("SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET not found in environment variables")
                
            if not self.access_token:
                print("No access token found. You'll need to complete the OAuth flow.")
                print(f"""
                1. Copy your Client ID and Client Secret from your Partners dashboard
                2. Add them to your .env file as SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET
                3. Run the setup_oauth() function to get an access token
                """)
                raise ValueError("SHOPIFY_ACCESS_TOKEN not found in environment variables")
            
            self.admin_token = self.access_token
            # Suppress log
            # masked_token = f"{self.admin_token[:4]}...{self.admin_token[-4:]}" if len(self.admin_token) > 8 else "****"
            # print(f"Using OAuth access token: {masked_token}")
        else:
            # Use admin token (old method)
            self.admin_token = os.getenv('SHOPIFY_ADMIN_TOKEN')
            if not self.admin_token:
                raise ValueError("SHOPIFY_ADMIN_TOKEN not found in environment variables")
            
            # Suppress log
            # Print a masked version of the token for debugging
            # masked_token = f"{self.admin_token[:4]}...{self.admin_token[-4:]}" if len(self.admin_token) > 8 else "****"
            # print(f"Using admin token: {masked_token}")
        
        self.endpoint = f"https://{self.shop_domain}/admin/api/2025-04/graphql.json"
        # Suppress log
        # print(f"Using GraphQL endpoint: {self.endpoint}")
        
    def execute_query(self, query):
        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': self.admin_token
        }
        
        response = requests.post(
            self.endpoint,
            json={'query': query},
            headers=headers,
            verify=False  # Disable SSL verification - Note: This should be properly configured in production
        )
        
        if response.status_code == 200:
            result = response.json()
            # Check for GraphQL errors
            if "errors" in result:
                print(f"GraphQL Errors: {json.dumps(result['errors'], indent=2)}")
            return result
        else:
            raise Exception(f"Query failed with status code: {response.status_code}\nResponse: {response.text}")

def exchange_code_for_token(client_id, client_secret, code, shop):
    """Exchange OAuth code for a permanent access token"""
    url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code
    }
    
    response = requests.post(url, data=payload, verify=False)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Failed to exchange code for token: {response.status_code}\nResponse: {response.text}")

def setup_oauth():
    """Set up OAuth for Shopify partner app"""
    client_id = os.getenv('SHOPIFY_CLIENT_ID')
    client_secret = os.getenv('SHOPIFY_CLIENT_SECRET')
    shop = "gamersupps.myshopify.com"  # Using development store
    redirect_uri = "http://localhost:8000/callback"  # You'll need to set up a local server to handle this
    
    if not client_id or not client_secret:
        raise ValueError("SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET must be set in your .env file")

    # Required scopes for accessing the discount functions
    scopes = "write_discounts,read_discounts,write_products,read_products"
    
    # Construct the authorization URL
    auth_url = f"https://{shop}/admin/oauth/authorize?client_id={client_id}&scope={scopes}&redirect_uri={redirect_uri}"
    
    print("\n============== SHOPIFY OAUTH SETUP ==============")
    print("Since you're running in WSL, please manually copy and paste this URL into your browser:")
    print("\n" + auth_url + "\n")
    
    print("After authorizing, you'll be redirected to a callback URL.")
    print("Since you may not have a localhost server running, you have two options:")
    
    choice = input("\nDo you want to: \n1. Manually enter the code after redirection\n2. Start a temporary local server to capture the code\nEnter 1 or 2: ")
    
    if choice.strip() == "1":
        print("\nManual code entry selected.")
        print("After authorizing in your browser, copy the 'code' parameter from the redirect URL.")
        print("The URL will look like: http://localhost:8000/callback?code=SOME_CODE&shop=your-shop.myshopify.com")
        
        code = input("\nEnter the code from the URL: ").strip()
        if not code:
            print("No code entered. Aborting.")
            return
            
        try:
            access_token = exchange_code_for_token(client_id, client_secret, code, shop)
            print(f"\nSuccessfully obtained access token: {access_token[:4]}...{access_token[-4:]}")
            print("\nAdd this to your .env file as:")
            print(f"SHOPIFY_ACCESS_TOKEN={access_token}")
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
    
    elif choice.strip() == "2":
        print("\nStarting temporary server to capture the callback...")
        # Set up variables to share between main thread and server
        code_received = {"code": None}
        server_stopped = threading.Event()
        
        # Create a request handler to capture the code
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                query = urlparse(self.path).query
                params = parse_qs(query)
                
                if 'code' in params:
                    code_received["code"] = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>You may close this window now.</p></body></html>")
                    server_stopped.set()
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Authorization failed!</h1><p>No code received.</p></body></html>")
                    
            # Silence server logs
            def log_message(self, format, *args):
                return
        
        # Start server in a separate thread
        port = 8000
        httpd = socketserver.TCPServer(("", port), CallbackHandler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"Local server started on port {port}. Now open the authorization URL in your browser.")
        print("Waiting for callback (timeout in 60 seconds)...")
        
        # Wait for the callback or timeout
        server_stopped.wait(timeout=60)
        httpd.shutdown()
        
        if code_received["code"]:
            try:
                access_token = exchange_code_for_token(client_id, client_secret, code_received["code"], shop)
                print(f"\nSuccessfully obtained access token: {access_token[:4]}...{access_token[-4:]}")
                print("\nAdd this to your .env file as:")
                print(f"SHOPIFY_ACCESS_TOKEN={access_token}")
            except Exception as e:
                print(f"Error exchanging code for token: {e}")
        else:
            print("No code received. Authorization failed or timed out.")
    
    else:
        print("Invalid choice. Please run the setup again and select 1 or 2.")

# Disable SSL verification warnings
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def check_store_access():
    query = """
    {
      shop {
        name
        myshopifyDomain
        plan {
          displayName
        }
      }
    }
    """
    return query

def list_installed_apps():
    query = """
    {
      appInstallations(first: 25) {
        edges {
          node {
            app {
              title
              id
            }
            accessScopes {
              handle
            }
          }
        }
      }
    }
    """
    return query

def query_discount_functions():
    query = """
    {
      codeDiscountNodes(first: 10) {
        edges {
          node {
            id
            codeDiscount {
              ... on DiscountCodeApp {
                title
                status
                discountClass
                codes(first: 5) {
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
              }
            }
          }
        }
      }
    }
    """
    return query

def check_function_by_id(function_id):
    query = """
    query GetFunctionById {
      shopifyFunction(id: "%s") {
        id
        title
        apiType
        app {
          title
        }
      }
    }
    """ % function_id
    return query

def get_store_functions():
    query = """
    query QueryStoreFunctions {
        shopifyFunctions(first: 50) {
            nodes {
                app {
                    title
                }
                apiType
                title
                id
            }
        }
    }
    """
    return query

def create_partner_code():
    mutation = """
    mutation NewParnerCodeCreation{
        discountCodeAppCreate(
            codeAppDiscount: {
                title: "Partner Code Programmatic - schwrca"
                functionId: "2ac7f32e-3b6b-48b3-a7d3-ea8fba68e876"
                startsAt: "2025-04-30T00:00:00"
                combinesWith: {
                    orderDiscounts: true
                    productDiscounts: false
                }
                code:"arthur-code"
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
    return mutation

def create_basic_discount():
    mutation = """
    mutation discountCodeBasicCreate {
      discountCodeBasicCreate(
        basicCodeDiscount: {
          title: "10OFF Basic Discount"
          code: "10OFFBASIC"
          startsAt: "2025-01-01T00:00:00Z"
          customerSelection: { all: true }
          customerGets: {
            value: { percentage: 0.10 }
            items: { all: true }
          }
        }
      ) {
        codeDiscountNode {
          codeDiscount {
            ... on DiscountCodeBasic {
              title
              codes(first: 1) {
                edges {
                  node {
                    code
                  }
                }
              }
              startsAt
              endsAt
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    return mutation

def check_api_access_scopes():
    query = """
    {
      currentAppInstallation {
        accessScopes {
          handle
        }
      }
    }
    """
    return query

def query_app_extensions():
    query = """
    {
      app {
        id
        title
        apiKey
        handle
      }
      currentAppInstallation {
        id
        metafields(first: 5) {
          edges {
            node {
              id
              key
              namespace
            }
          }
        }
      }
    }
    """
    return query

def query_app_functions():
    query = """
    {
      appInstallations(first: 10) {
        edges {
          node {
            id
            app {
              id
              title
              handle
            }
          }
        }
      }
      shopifyFunctions(first: 10) {
        nodes {
          id
          title
          apiType
          app {
            title
          }
        }
      }
    }
    """
    return query

def get_detailed_functions(first=50):
    """
    Get detailed information about Shopify Functions including their configuration
    """
    query = f"""
    query GetDetailedFunctions {{
        shopifyFunctions(first: {first}) {{
            nodes {{
                id
                title
                apiType
                app {{
                    title
                    id
                    handle
                    developerName
                }}
                appVersion
                status
                configurationSchema
                createdAt
                metafields(first: 5) {{
                    edges {{
                        node {{
                            namespace
                            key
                            value
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    return query

def get_function_by_id(function_id):
    """
    Get detailed information about a specific Shopify Function by its ID
    The function_id should be the UUID part, not the full gid
    """
    query = f"""
    query GetFunctionDetails {{
        shopifyFunction(id: "gid://shopify/ShopifyFunction/{function_id}") {{
            id
            title
            apiType
            app {{
                title
                id
                handle
                developerName
            }}
            appVersion
            status
            configurationSchema
            createdAt
            metafields(first: 5) {{
                edges {{
                    node {{
                        namespace
                        key
                        value
                    }}
                }}
            }}
        }}
    }}
    """
    return query

def show_help():
    print("""
Shopify GraphQL API Client

Usage:
  python shopify_graphql.py [options]

Options:
  --setup-oauth            Run the OAuth setup flow to get an access token
  --detailed               Get detailed information about all Shopify Functions
  --function-id <id>       Get detailed information about a specific Shopify Function
                           Use the UUID part (not the full gid)
  --help                   Show this help message

Examples:
  python shopify_graphql.py                            # Run standard queries
  python shopify_graphql.py --detailed                 # Get detailed information about all functions
  python shopify_graphql.py --function-id c7323059-4c5b-4670-903b-d8656cbef77b  # Query a specific function
    """)

def main():
    # Show help if requested
    if "--help" in os.sys.argv or "-h" in os.sys.argv:
        show_help()
        return
        
    # Check if we need to set up OAuth
    if "--setup-oauth" in os.sys.argv:
        setup_oauth()
        return
    
    # Check if we want to query a specific function by ID
    function_id = None
    for i, arg in enumerate(os.sys.argv):
        if arg == "--function-id" and i+1 < len(os.sys.argv):
            function_id = os.sys.argv[i+1]
    
    # Create client with partner authentication
    try:
        client = ShopifyGraphQLClient(use_partner_auth=True)
    except Exception as e:
        print(f"Partner app authentication failed: {e}")
        client = ShopifyGraphQLClient(use_partner_auth=False)
    
    # Test basic store access - suppressed
    try:
        client.execute_query(check_store_access())
    except Exception as e:
        print(f"Error testing store access: {e}")
    
    # Check API scopes - suppressed
    try:
        client.execute_query(check_api_access_scopes())
    except Exception as e:
        print(f"Error checking API scopes: {e}")
    
    # Try to query app extensions - suppressed
    try:
        client.execute_query(query_app_extensions())
    except Exception as e:
        print(f"Error querying app extensions: {e}")
    
    # If a specific function ID was provided, query just that function
    if function_id:
        print(f"\nQuerying function with ID: {function_id}")
        try:
            result = client.execute_query(get_function_by_id(function_id))
            print(json.dumps(result, indent=2))
            return
        except Exception as e:
            print(f"Error querying function by ID: {e}")
            return
    
    # If --detailed flag is set, use the detailed query
    if "--detailed" in os.sys.argv:
        print("\nGetting detailed information about Shopify Functions...")
        try:
            result = client.execute_query(get_detailed_functions())
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error getting detailed functions: {e}")
        return
        
    # Fetch store functions - This is the part that works
    print("\nFetching store functions...")
    try:
        result = client.execute_query(get_store_functions())
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error fetching store functions: {e}")
    
    # If user requests it, we can query specific functions based on the IDs we found
    if "--query-ids" in os.sys.argv:
        print("\nQuerying functions from specific IDs...")
        try:
            # Extract IDs from the previous result to build a dynamic query
            nodes = result.get('data', {}).get('shopifyFunctions', {}).get('nodes', [])
            if nodes:
                query = "{\n"
                for i, node in enumerate(nodes):
                    function_id = node.get('id')
                    if function_id:
                        query += f'  function{i}: shopifyFunction(id: "gid://shopify/ShopifyFunction/{function_id}") {{\n'
                        query += '    id\n    title\n    apiType\n  }\n'
                query += "}"
                
                result = client.execute_query(query)
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error querying specific functions: {e}")

if __name__ == "__main__":
    main() 