from typing import TypedDict, Literal, Optional, Any


class Payload(TypedDict):
    network: int
    phone: str 
    data_plan: int
    bypass: bool
    request_id: str
    metadata: Optional[Any]

Networks = Literal['MTN', 'GLO', 'AIRTEL', '9MOBILE']


class ResponseData(TypedDict):
    network: str
    request_id: str
    amount: str
    dataplan: str
    status: Literal['success', 'fail', 'pending']
    transid: str
    message: str
    phone_number: str
    oldbal: int
    newbal: int
    system: str
    plan_type: Literal['COOPERATE GIFTING', 'SME']
    wallet_vending: Literal['wallet', 'bonus', 'cashback']
    response: str


class AirtimeResponse(TypedDict):
    network: str
    request_id: str
    amount: str
    discount: int
    status: Literal['success', 'fail']
    transid: Optional[str]
    message: str
    phone_number: str
    oldbal: int
    newbal: int
    system: str
    plan_type: Literal['VTU']
    wallet_vending: Literal['wallet', 'bonus', 'cashback']
    response: Optional[str]


GsubServiceID = Literal[
    'mtn_sme',
    'mtn_cg_lite', 
    'mtn_gifting',
    'mtn_datashare',
    'mtn_coupon',
    'mtncg',
    'airtel_cg',
    'airtel_sme',
    'glo_data',
    'glo_sme',
    'etisalat_data'
]


class GsubResponse(TypedDict):
    code: int
    status: Literal['success', 'failed', 'pending']
    transactionID: str
    amount: float
    phone: str
    serviceID: GsubServiceID
    amountPaid: float
    initialBalance: float
    finalBalance: float
    date: str
    api_response: str


class Content(TypedDict):
    transactionID: int
    requestID: str
    amount: str
    phone: str
    serviceID: GsubServiceID
    amountPaid: float
    initialBalance: str
    finalBalance: float
    image: str
    fee: str
    serviceName: str
    status: str
    code: int
    description: str
    date: str
    diplayValue: Any


class Gateway(TypedDict):
    referrer: str


class GsubDataResponse(TypedDict):
    code: int
    status: str
    description: str
    content: Content
    gateway: Gateway


class GsubRequeryResponse(TypedDict):
    code: str
    status: str
    description: str
    api_response: str


class GsubPayload(TypedDict):
    serviceID: GsubServiceID
    plan: str
    api: Optional[str]
    amount: Optional[str]
    phone: str
    requestID: str


class Plan(TypedDict):
    displayName: str  # Type hint for f-string literal
    value: str
    price: str


class VariationResponse(TypedDict):
    service: str
    PlanName: str
    fixedPrice: bool
    plans: list[Plan]


class Pin(TypedDict):
    pin: str
    sn: str


class GsubEpinResponse(TypedDict):
    message: str
    status: str
    id: str
    network: str
    value: str
    number: str
    delivered: str
    pending: int
    pins: list[Pin]
