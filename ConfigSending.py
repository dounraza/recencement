from __future__ import print_function
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from dotenv import dotenv_values

  
config = dotenv_values(".env")
# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
# Configure API key authorization: api-key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = config['API_KEY_BREVO']
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['api-key'] = 'Bearer'
# Configure API key authorization: partner-key
# configuration = sib_api_v3_sdk.Configuration()
# configuration.api_key['partner-key'] = config['API_KEY_BREVO']
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['partner-key'] = 'Bearer'

# create an instance of the API class
api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))

try:
    # Get your account information, plan and credits details
    api_response = api_instance.get_account()
    print(api_response)
   
except ApiException as e:
    print("Exception when calling AccountApi->get_account: %s\n" % e)
    
   