# GoAffPro API Client

A Python client for interacting with the GoAffPro affiliate marketing API.

## Features

- Retrieve all affiliates with pagination support
- Get detailed information about a specific affiliate
- Fetch discount codes for any affiliate
- Save results to JSON for further analysis
- Command-line interface for easy usage

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The script provides a command-line interface for easy access to the API:

```bash
# Get all affiliates and their codes (saves to a timestamped JSON file)
python goaff_api.py all

# Get all affiliates without saving to file
python goaff_api.py all --no-save

# Get details for a single affiliate by ID
python goaff_api.py affiliate 12345

# Get discount codes for a specific affiliate
python goaff_api.py codes 12345

# Show help
python goaff_api.py --help
```

### Using as a Library

You can also import the functions and use them in your own code:

```python
from goaff_api import get_affiliates, get_affiliate, get_affiliate_codes

# Get all affiliates
all_affiliates = get_affiliates()

# Get a specific affiliate
affiliate = get_affiliate("12345")

# Get codes for an affiliate
codes = get_affiliate_codes("12345")
```

## API Token

The script currently uses a hardcoded API token. For security in a production environment, consider:

1. Using environment variables
2. Creating a configuration file that is not tracked in version control
3. Using a secure secret management solution

### Authentication

GoAffPro API requires authentication via the `x-goaffpro-access-token` header. You can generate an API token from the GoAffPro dashboard under Settings -> Advanced Settings tab -> API Keys section.

## API Endpoints

The client interacts with the following GoAffPro API endpoints:

- `GET /v1/admin/affiliates` - List all affiliates (paginated)
- `GET /v1/admin/affiliates/{id}` - Get a specific affiliate
- `GET /v1/admin/affiliates/{id}/codes` - Get codes for a specific affiliate

See the [GoAffPro API documentation](https://api.goaffpro.com/docs/admin/#/affiliate/get_admin_affiliates) for more details. 