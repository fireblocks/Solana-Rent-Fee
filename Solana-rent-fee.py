import json
#import rsa
import base64
import urllib3

FIREBLOCKS_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA0+6wd9OJQpK60ZI7qnZG
jjQ0wNFUHfRv85Tdyek8+ahlg1Ph8uhwl4N6DZw5LwLXhNjzAbQ8LGPxt36RUZl5
YlxTru0jZNKx5lslR+H4i936A4pKBjgiMmSkVwXD9HcfKHTp70GQ812+J0Fvti/v
4nrrUpc011Wo4F6omt1QcYsi4GTI5OsEbeKQ24BtUd6Z1Nm/EP7PfPxeb4CP8KOH
clM8K7OwBUfWrip8Ptljjz9BNOZUF94iyjJ/BIzGJjyCntho64ehpUYP8UJykLVd
CGcu7sVYWnknf1ZGLuqqZQt4qt7cUUhFGielssZP9N9x7wzaAIFcT3yQ+ELDu1SZ
dE4lZsf2uMyfj58V8GDOLLE233+LRsRbJ083x+e2mW5BdAGtGgQBusFfnmv5Bxqd
HgS55hsna5725/44tvxll261TgQvjGrTxwe7e5Ia3d2Syc+e89mXQaI/+cZnylNP
SwCCvx8mOM847T0XkVRX3ZrwXtHIA25uKsPJzUtksDnAowB91j7RJkjXxJcz3Vh1
4k182UFOTPRW9jzdWNSyWQGl/vpe9oQ4c2Ly15+/toBo4YXJeDdDnZ5c/O+KKadc
IMPBpnPrH/0O97uMPuED+nI6ISGOTMLZo35xJ96gPBwyG5s2QxIkKPXIrhgcgUnk
tSM7QYNhlftT4/yVvYnk0YcCAwEAAQ==
-----END PUBLIC KEY-----
"""
#DESTINATION_URL = "https://7c82a5ed-4d8c-476d-ad09-9085d711addb.mock.pstmn.io/fireblocks-webhook"
#DESTINATION_NOTIF_URL = "https://7c82a5ed-4d8c-476d-ad09-9085d711addb.mock.pstmn.io/fireblocks-webhook"
# DESTINATION_URL = "https://fe0370e7-5a02-4a42-8168-4f4fa68316f5.mock.pstmn.io/fireblocks-webhook"
# DESTINATION_NOTIF_URL = "https://fe0370e7-5a02-4a42-8168-4f4fa68316f5.mock.pstmn.io/fireblocks-webhook"
DESTINATION_URL = "https://58d9123e-7aab-4c1c-960c-1ae4aadb9c87.mock.pstmn.io/solana"
DESTINATION_NOTIF_URL = "https://58d9123e-7aab-4c1c-960c-1ae4aadb9c87.mock.pstmn.io/solana"
#signature_pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(FIREBLOCKS_PUBLIC_KEY)


def signature_is_valid(body, signature):
    try:
        hashing_alg = rsa.verify(body, base64.b64decode(signature), signature_pub_key)
        return hashing_alg == "SHA-512"
    except rsa.pkcs1.VerificationError:
        return False


def delete_postman_mock_server_headers(headers):
    unnecessary_headers = [
        'x-amzn-tls-version', 'x-amzn-tls-cipher-suite', 'x-forwarded-proto',
        'x-forwarded-port', 'x-forwarded-for', 'content-length', 'x-amzn-trace-id',
        'host', 'X-Forwarded-Proto', 'X-Forwarded-Port', 'X-Forwarded-For',
        'Content-Length', 'X-Amzn-Trace-Id', 'Host'
    ]
    for header in unnecessary_headers:
        headers.pop(header, None)
    print ("popped headers is", headers)
    return headers


def get_transaction_rent_exempt_fee(transaction_hash):
    # Solana RPC URL (replace with your own if required)
#    solana_rpc_url = "https://api.mainnet-beta.solana.com"
    solana_rpc_url = "https://api.devnet.solana.com"
    print ("solana_rpc_url is", solana_rpc_url)

    # Query transaction details
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [transaction_hash, {"encoding": "json", "commitment": 'confirmed'}]
    }
    encoded_data = json.dumps(payload)
    http = urllib3.PoolManager()
#    response = urllib3.post(solana_rpc_url, json=payload)
    response = http.request("POST", solana_rpc_url, body=encoded_data, headers={"Content-Type": "application/json"})
    response_data = json.loads(response.data.decode('utf-8'))
    print ("solana response is", json.dumps(response_data, indent=4))
    if response.status == 200:
        result = response_data.get("result", {})
        #result = response.json().get("result", {})
        rent_exempt_fee = result.get("meta", {}).get("fee", None)

        # Extract rent-exempt fee from transaction meta
        #rent_exempt_fee = result.get("meta", {}).get("postBalances", [])[0]
        print ("rent_exempt_fee response is", rent_exempt_fee)
        return rent_exempt_fee
    else:
        raise Exception("Failed to fetch transaction details from Solana RPC")


def lambda_handler(event, context):
    print ("Event is", event)
    body = event['body']
    if event.get('isBase64Encoded', False):
        body = base64.b64decode(body).decode('utf-8')
    print("Full request body:", body)
    print("Raw body:", event['body'])
    header_part = event['headers']

    body_part = str.encode(body)
    body_json = json.loads(body)

    print("body_part", body_part)
    print("body_json", body_json)

#    if 'fireblocks-signature' in header_part:
#        sig = header_part['fireblocks-signature']
#        if not signature_is_valid(body=body_part, signature=sig):
#            return {"statusCode": 403, "body": "Invalid signature"}


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

  # Check if 'event_type' is 'TRANSACTION_STATUS_UPDATED'
    if event_type != 'TRANSACTION_STATUS_UPDATED':
        print("Event type is not 'TRANSACTION_CREATED'. Ignoring.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event type not relevant'}),
            'isBase64Encoded': False
        }

    # Check if 'asset_id' is 'SOL_TEST'
    if asset_id != 'SOL_TEST':
        print("Asset ID is not 'SOL_TEST'. Ignoring.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Asset ID not relevant'}),
            'isBase64Encoded': False
        }

    # Check if 'tx_hash' exists and is not empty
    if not tx_hash:
        print("Transaction hash is missing or empty. Ignoring.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Transaction hash missing or empty'}),
            'isBase64Encoded': False
        }


    notifications_secret = 'x-webhook-secret' in header_part

    transaction_hash = body_json.get("transaction_hash")
    # transaction_hash = "4hUJU1PoPQJwtcUkonw7vDaBK8PtHvxVNS4SDRofDdhXz9Mx6dg3hjmVRuPuBfQYRFUHSbK5b8suRsuPA9cg9hdp"
    print ("txn hash is", transaction_hash)
    if not transaction_hash:
        return {"statusCode": 400, "body": "Transaction hash missing"}

    try:
        rent_exempt_fee = get_transaction_rent_exempt_fee(transaction_hash)
    except Exception as e:
        return {"statusCode": 500, "body": f"Error fetching transaction details: {str(e)}"}

    http = urllib3.PoolManager()

    # Add the rent-exempt fee to the ping-access-token header
    copy_header = header_part.copy()
    print ("copy_header is", copy_header)
    copy_header['rent-exempt-fee'] = str(rent_exempt_fee)
    copy_header = delete_postman_mock_server_headers(copy_header)

    url = DESTINATION_NOTIF_URL if notifications_secret else DESTINATION_URL
    print ("body is", body_part)
    print ("headers is", copy_header)
    response = http.request("POST", url, body=body_part, headers=copy_header)

    return {
        'statusCode': response.status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'status': 'ok'}),
        'isBase64Encoded': False
    }





