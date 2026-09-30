import tinytuya
import json

API_KEY = 'my8fcvcjnatcvpcpamct'
API_SECRET = '1ecfee16d7fe4081b98c5d669f587d72'
REGION = 'us' 
USER_ID = 'az1733391445487QkU2x'

try:
    c = tinytuya.Cloud(
        apiRegion=REGION,
        apiKey=API_KEY,
        apiSecret=API_SECRET
    )
    
    # Direct request to the devices endpoint using the provided User ID
    url = f'/v1.0/users/{USER_ID}/devices'
    response = c.cloudrequest(url)
    
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error: {e}")
