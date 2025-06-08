RESPONSE_CODES = {
    '085': {
        'message': 'Invalid Device time, Please ensure that your device time is properly set in the 24 Hour format or GMT + 1.',
        'title': 'TIME_NOT_CORRECT'
    },
    '016': {
        'message': 'Transaction failed, please verify your details and try again.',
        'title': 'TRANSACTION_FAILED'
    },
    '000': {
        'message': 'Transaction completed successfully. Thank you for choosing isubscribe!',
        'title': 'TRANSACTION_SUCCESSFUL'
    },
    '010': {
        'message': 'It appears the Product you selected does not exist in stock, please choose another one.',
        'title': 'NO_PRODUCT_VARIATION'
    },
    '012': {
        'message': 'It appears the Product you selected does not exist, please choose another one.',
        'title': 'PRODUCT_DOES_NOT_EXIST'
    },
    '018': {
        'message': 'This service provider is currently unavailable, please try again later.',
        'title': 'LOW_WALLET_BALANCE'
    },
    '099': {
        'message': 'This transaction is pending.',
        'title': 'TRANSACTION_PENDING'
    }
}
