from typing import TypedDict, Literal, Union, List
from typing_extensions import NotRequired
from typing import TypedDict, Literal, Union, Optional

class Transaction(TypedDict):
    status: Literal['initiated', 'pending', 'delivered', 'failed', 'success']
    product_name: str
    unique_element: str
    unit_price: float
    quantity: int
    service_verification: Optional[str]
    channel: str
    commission: float
    total_amount: float
    discount: Optional[str]
    type: str
    email: str
    phone: str
    name: Optional[str]
    convinience_fee: float
    amount: float
    platform: str
    method: str
    transactionId: str

class TransactionDate(TypedDict):
    date: str
    timezone_type: int
    timezone: str

VTPassServiceName = Literal[
    'mtn-data', 'glo-data', 'airtel-data', '9mobile-data',
    'etisalat-data', 'glo-sme-data', '9mobile-sme-data', 'smile-direct'
]

class VTPassVariation(TypedDict):
    variation_code: str
    name: str
    variation_amount: str
    fixedPrice: Literal['Yes', 'No']

class VTPassVariationServiceContent(TypedDict):
    ServiceName: str
    serviceID: VTPassServiceName
    convinience_fee: str
    varations: List[VTPassVariation]

class VTPassVariationServiceResponse(TypedDict):
    response_description: str
    content: VTPassVariationServiceContent

class VTPassTransactionRequest(TypedDict):
    request_id: str
    serviceID: str
    billersCode: str
    variation_code: str
    amount: NotRequired[int]
    phone: Union[int, str]
    subscription_type: NotRequired[Literal['Change', 'Renew']]

class VTPassAirtimeTransactionRequest(TypedDict):
    request_id: str
    serviceID: Literal['glo', 'mtn', 'airtel', 'etisalat']
    amount: NotRequired[int]
    phone: Union[int, str]

class VTPassAirtimeTransactionResponse(TypedDict):
    code: str
    response_description: str
    requestId: str
    transactionId: str
    amount: str
    transaction_date: TransactionDate
    purchased_code: str

class VTPassTransactionResponseContent(TypedDict):
    transactions: Transaction

class VTPassCard(TypedDict):
    Serial: str
    Pin: str

class VTPassTransactionResponse(TypedDict):
    code: str
    content: VTPassTransactionResponseContent
    response_description: str
    requestId: str
    amount: str
    transaction_date: TransactionDate
    purchased_code: str

    token: NotRequired[str]
    Token: NotRequired[str]
    MainToken: NotRequired[str]
    mainToken: NotRequired[str]

    Pin: NotRequired[str]

    tokens: NotRequired[List[str]]
    cards: NotRequired[List[VTPassCard]]


class VTPassCommissionDetails(TypedDict):
    amount: Optional[str]
    rate: str
    rate_type: str
    computation_type: str

class VTPassMerchantVerifyContent(TypedDict):
    Customer_Name: str
    Address: str
    MeterNumber: str
    Min_Purchase_Amount: int
    Outstanding: int
    Customer_Arrears: Optional[str]
    Meter_Type: str
    WrongBillersCode: bool
    commission_details: VTPassCommissionDetails

class MerchantVerifyResponse(TypedDict):
    code: str
    content: VTPassMerchantVerifyContent