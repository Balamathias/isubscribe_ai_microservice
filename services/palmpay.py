import json
import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import requests
from nanoid import generate
from utils.signature import generate_palm_pay_signature
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PalmPayCreateAccountRequest:
    customer_name: str
    email: str


@dataclass
class PalmPayCreateAccountData:
    identity_type: str
    license_number: str
    virtual_account_name: str
    virtual_account_no: str
    email: str
    customer_name: str
    status: str
    account_reference: str


@dataclass
class PalmPayCreateAccountResponse:
    data: PalmPayCreateAccountData
    resp_msg: str
    resp_code: str
    status: bool


class PalmPayService:
    def __init__(self):
        self.base_url = "https://open-gw-prod.palmpay-inc.com"
        # self.base_url = "https://open-gw-daily.palmpay-inc.com"  # For testing
        self.app_id = os.getenv("PALMPAY_APP_ID")
        self.private_key = os.getenv("PALMPAY_PRIVATE_KEY")
        self.license_number = os.getenv("LICENSE_NUMBER", "")

    def create_virtual_account(self, request_data: PalmPayCreateAccountRequest) -> PalmPayCreateAccountResponse:
        request_body = {
            "customerName": request_data.customer_name,
            "email": request_data.email,
            "requestTime": int(time.time() * 1000),
            "version": "V2.0",
            "identityType": "company",
            "licenseNumber": self.license_number,
            "virtualAccountName": request_data.customer_name,
            "nonceStr": generate(size=32),
        }

        signature = generate_palm_pay_signature(request_body, self.private_key if self.private_key else "")

        headers = {
            "Authorization": f"Bearer {self.app_id}",
            "countryCode": "NG",
            "Signature": signature,
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v2/virtual/account/label/create",
                headers=headers,
                json=request_body,
                timeout=30
            )

            response.raise_for_status()
            
            response_data = response.json()
            print(f"PalmPay response: {response_data}")
            
            return PalmPayCreateAccountResponse(
                data=PalmPayCreateAccountData(
                    identity_type=response_data["data"]["identityType"],
                    license_number=response_data["data"]["licenseNumber"],
                    virtual_account_name=response_data["data"]["virtualAccountName"],
                    virtual_account_no=response_data["data"]["virtualAccountNo"],
                    email=response_data["data"]["email"],
                    customer_name=response_data["data"]["customerName"],
                    status=response_data["data"]["status"],
                    account_reference=response_data["data"]["accountReference"],
                ),
                resp_msg=response_data["respMsg"],
                resp_code=response_data["respCode"],
                status=response_data["status"]
            )

        except requests.RequestException as error:
            print(f"PalmPay API error: {error}")
            raise error
        