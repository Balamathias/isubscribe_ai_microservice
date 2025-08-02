import os
from typing import Any, Dict
import requests
from requests.exceptions import ConnectionError, HTTPError
from dotenv import load_dotenv

from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

load_dotenv()

session = requests.Session()

session.headers.update(
    {
        "Authorization": f"Bearer {os.getenv('EXPO_TOKEN')}",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
)

def send_push(data: Dict[str, Any]) -> None:
    try:
        response = PushClient(session=session).publish(
            PushMessage(**data))
        
    except PushServerError as exc:
        print(f"Push server error: {exc.errors}")
        raise exc
    
    except (ConnectionError, HTTPError) as exc:
        print(f"Connection or HTTP error: {exc}")
        raise exc
    
    except DeviceNotRegisteredError:
        # Handle device not registered error
        print("Device not registered")
        # Optionally, you can mark the token as inactive in your database
        # from notifications.models import PushToken
        # PushToken.objects.filter(token=data['to']).update(active=False)
        raise DeviceNotRegisteredError("Device not registered for push notifications")
    
    except PushTicketError as exc:
        # Handle other push ticket errors
        print(f"Push ticket error: {exc.push_response._asdict()}")
        raise exc
    
        
# Basic arguments. You should extend this function with the push features you
# want to use, or simply pass in a `PushMessage` object.
# def send_push_message(token, message, extra=None):
#     try:
#         response = PushClient(session=session).publish(
#             PushMessage(to=token,
#                         body=message,
#                         data=extra))
#     except PushServerError as exc:
#         # Encountered some likely formatting/validation error.
#         rollbar.report_exc_info(
#             extra_data={
#                 'token': token,
#                 'message': message,
#                 'extra': extra,
#                 'errors': exc.errors,
#                 'response_data': exc.response_data,
#             })
#         raise
#     except (ConnectionError, HTTPError) as exc:
#         # Encountered some Connection or HTTP error - retry a few times in
#         # case it is transient.
#         rollbar.report_exc_info(
#             extra_data={'token': token, 'message': message, 'extra': extra})
#         raise self.retry(exc=exc)

#     try:
#         # We got a response back, but we don't know whether it's an error yet.
#         # This call raises errors so we can handle them with normal exception
#         # flows.
#         response.validate_response()
#     except DeviceNotRegisteredError:
#         # Mark the push token as inactive
#         from notifications.models import PushToken
#         PushToken.objects.filter(token=token).update(active=False)
#     except PushTicketError as exc:
#         # Encountered some other per-notification error.
#         rollbar.report_exc_info(
#             extra_data={
#                 'token': token,
#                 'message': message,
#                 'extra': extra,
#                 'push_response': exc.push_response._asdict(),
#             })
#         raise self.retry(exc=exc)