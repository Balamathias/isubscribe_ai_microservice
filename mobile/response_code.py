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


GSUB_RESPONSE_CODES = {
    '204': {
        'message': 'Required content not sent. Please check your request parameters.',
        'title': 'REQUIRED_CONTENT_NOT_SENT'
    },
    '206': {
        'message': 'Invalid content provided. Please verify your request data.',
        'title': 'INVALID_CONTENT'
    },
    '401': {
        'message': 'Invalid plan selected. Please choose a valid plan.',
        'title': 'INVALID_PLAN'
    },
    '402': {
        'message': 'Insufficient balance to complete this transaction.',
        'title': 'INSUFFICIENT_BALANCE'
    },
    '404': {
        'message': 'Requested content not found.',
        'title': 'CONTENT_NOT_FOUND'
    },
    '405': {
        'message': 'Invalid request method. Only POST requests are allowed.',
        'title': 'REQUEST_METHOD_NOT_IN_POST'
    },
    '406': {
        'message': 'This service is currently disabled. Please try again later.',
        'title': 'SERVICE_DISABLED'
    },
    '502': {
        'message': 'Gateway error occurred. Please try again later.',
        'title': 'GATEWAY_ERROR'
    }
}
