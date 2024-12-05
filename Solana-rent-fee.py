import json
import base64
import urllib3
from urllib3.util import Timeout

DESTINATION_URL = "https://58d9123e-7aab-4c1c-960c-1ae4aadb9c87.mock.pstmn.io/solana"
DESTINATION_NOTIF_URL = "https://58d9123e-7aab-4c1c-960c-1ae4aadb9c87.mock.pstmn.io/solana"


def get_transaction_rent_exempt_fee(transaction_hash):
    solana_rpc_url = "https://api.devnet.solana.com"
    print("Solana RPC URL is", solana_rpc_url)

    # Query transaction details
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [transaction_hash, {"encoding": "json", "commitment": 'confirmed'}]
    }
    encoded_data = json.dumps(payload)
    http = urllib3.PoolManager(timeout=Timeout(connect=5.0, read=10.0))

    try:
        print("Sending request to Solana RPC")
        response = http.request("POST", solana_rpc_url, body=encoded_data, headers={"Content-Type": "application/json"})
        print("Received response from Solana RPC")
    except urllib3.exceptions.HTTPError as e:
        print(f"Error connecting to Solana RPC: {e}")
        raise Exception("Failed to connect to Solana RPC")

    response_data = json.loads(response.data.decode('utf-8'))
    print("Solana response is", json.dumps(response_data, indent=4))
    if response.status == 200:
        result = response_data.get("result", {})
        meta = result.get("meta", {})
        post_balances = meta.get("postBalances", [])

        print("Post balances:", post_balances)
        if len(post_balances) > 4:
            rent_exempt_fee = post_balances[4]
            print(f"Rent-exempt fee extracted: {rent_exempt_fee}")

            # Check if rent_exempt_fee equals 2039280
            if rent_exempt_fee == 2039280:
                print("Rent-exempt fee matches 2039280. Proceeding.")
                return rent_exempt_fee
            else:
                print(f"Rent-exempt fee {rent_exempt_fee} does not equal 2039280. Exiting function.")
                return None  # Return None to indicate condition not met
        else:
            print("postBalances does not have enough elements. Exiting function.")
            return None
    else:
        raise Exception("Failed to fetch transaction details from Solana RPC")

def lambda_handler(event, context):
    print("Event is", event)
    body = event['body']
    if event.get('isBase64Encoded', False):
        body = base64.b64decode(body).decode('utf-8')
    print("Full request body:", body)
    header_part = event.get('headers', {})

    # Parse the body into JSON
    try:
        if isinstance(body, str):
            body_json = json.loads(body)  # Parse JSON string
        elif isinstance(body, dict):
            body_json = body  # Already a dict
        else:
            raise TypeError(f"Unexpected type for 'body': {type(body)}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid JSON in request body'}),
            'isBase64Encoded': False
        }
    
    # Prepare body_part for forwarding
    body_part = body.encode('utf-8') if isinstance(body, str) else json.dumps(body).encode('utf-8')

    print("body_part:", body_part)
    print("body_json:", body_json)

    # Extract top-level 'type' field
    event_type = body_json.get('type')
    print(f"Event Type: {event_type}")

    # Extract 'data' dictionary
    data = body_json.get('data', {})
    print(f"Data: {data}")

    # Extract 'assetId' from 'data'
    asset_id = data.get('assetId')
    print(f"Asset ID: {asset_id}")

    # Extract 'txHash' from 'data'
    tx_hash = data.get('txHash')
    print(f"Transaction Hash: {tx_hash}")

    # Check conditions
    if not tx_hash:
        print("Transaction hash missing or empty. Exiting.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Transaction hash missing or empty'}),
            'isBase64Encoded': False
        }

    if asset_id == 'SOL_USDC_JKVK':
        print(f"Asset ID '{asset_id}' is valid.")
    else:
        print("Asset ID is not valid. Exiting.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Asset ID not relevant'}),
            'isBase64Encoded': False
        }

    print("Conditions met. Proceeding with processing.")

    # Proceed to get transaction details
    try:
        rent_exempt_fee = get_transaction_rent_exempt_fee(tx_hash)
    except Exception as e:
        print(f"Error fetching transaction details: {e}")
        return {
            'statusCode': 500,
            'body': f"Error fetching transaction details: {str(e)}",
            'isBase64Encoded': False
        }

    # Prepare headers
    notifications_secret = 'x-webhook-secret' in header_part
    copy_header = header_part.copy()
    print("Original headers:", copy_header)
    copy_header['rent-exempt-fee'] = str(rent_exempt_fee)
    print("Modified headers:", copy_header)

    # Forward the notification
    url = DESTINATION_NOTIF_URL if notifications_secret else DESTINATION_URL
    print("Destination URL:", url)
    print("Forwarding body:", body_part)
    print("Forwarding headers:", copy_header)

    http = urllib3.PoolManager(timeout=Timeout(connect=5.0, read=10.0))

    try:
        print("Sending notification to destination URL")
        response = http.request("POST", url, body=body_part, headers=copy_header)
        print("Received response from destination URL")
    except urllib3.exceptions.HTTPError as e:
        print(f"Error connecting to destination URL: {e}")
        return {
            'statusCode': 500,
            'body': f"Error connecting to destination URL: {str(e)}",
            'isBase64Encoded': False
        }

    return {
        'statusCode': response.status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'status': 'ok'}),
        'isBase64Encoded': False
    }