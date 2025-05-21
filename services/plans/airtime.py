import os
import requests
from typing import Any, Dict, Optional, TypedDict, Literal, Union
from dotenv import load_dotenv

from pytypes.vtpass import (
    VTPassTransactionResponse
)

load_dotenv()

VTPASS_API_KEY = os.getenv("VTPASS_API_KEY")
VTPASS_SECRET_KEY = os.getenv("VTPASS_SECRET_KEY")
VTPASS_BASE_URL = os.getenv("VTPASS_BASE_URL")


class BuyAirtimeParams(TypedDict, total=False):
    request_id: str
    serviceID: Literal["glo", "mtn", "airtel", "etisalat"]
    phone: Union[int, str]
    amount: float


def buy_airtime(
    request_id: str,
    serviceID: Literal["glo", "mtn", "airtel", "etisalat"],
    phone: Union[int, str],
    amount: Optional[float] = None,
) -> Optional[VTPassTransactionResponse]:
    
    payload: BuyAirtimeParams = {
        "request_id": request_id,
        "serviceID": serviceID,
        "phone": phone,
    }

    if amount is not None:
        payload["amount"] = amount

    headers = {
        "api-key": VTPASS_API_KEY,
        "secret-key": VTPASS_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{VTPASS_BASE_URL}/pay", json=payload, headers=headers)
        print("AIRTSTATS:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to buy airtime: {res.text}")

        return res.json()
    except Exception as err:
        print(err)
        return None