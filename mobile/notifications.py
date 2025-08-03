import os
import json
from typing import Any, Dict, List, Union, Optional
import requests
from requests.exceptions import ConnectionError, HTTPError
from dotenv import load_dotenv

load_dotenv()

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

def send_push_notification(
    token: str, 
    title: str, 
    body: str, 
    subtitle: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a push notification using Expo's HTTP/2 API.
    
    Args:
        token: The Expo push token
        title: The notification title
        body: The notification body
        subtitle: Optional subtitle (iOS only)
        extra_data: Optional additional data to send with the notification
    
    Returns:
        Response from Expo push service
    
    Raises:
        HTTPError: If the request fails
        ConnectionError: If there's a connection issue
    """
    headers = {
        "host": "exp.host",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
    
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "badge": 1,
        'data': extra_data if extra_data else {}
    }
    
    if subtitle:
        payload["subtitle"] = subtitle
    
    if extra_data:
        payload["data"] = extra_data
    
    try:
        response = requests.post(
            EXPO_PUSH_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "errors" in result:
            print(f"Push notification errors: {result['errors']}")
            raise HTTPError(f"Push notification failed: {result['errors']}")
        
        if "data" in result:
            for ticket in result["data"]:
                if ticket.get("status") == "error":
                    error_details = ticket.get("details", {})
                    if error_details.get("error") == "DeviceNotRegistered":
                        print(f"Device not registered: {token}")
                        from services.supabase import superbase as supabase
                        try:
                            supabase.table('push_tokens').update({'active': False}).eq('token', token).execute()
                        except Exception as e:
                            print(f"Failed to update token status: {e}")
                    print(f"Push ticket error: {ticket}")
        
        return result
        
    except ConnectionError as exc:
        print(f"Connection error: {exc}")
        raise exc
    
    except HTTPError as exc:
        print(f"HTTP error: {exc}")
        raise exc


def send_bulk_push_notifications(
    notifications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Send multiple push notifications in a single request (up to 100).
    
    Args:
        notifications: List of notification dictionaries, each containing:
            - token: The Expo push token
            - title: The notification title
            - body: The notification body
            - subtitle: Optional subtitle (iOS only)
            - extra_data: Optional additional data
    
    Returns:
        Response from Expo push service
    
    Raises:
        ValueError: If more than 100 notifications are provided
        HTTPError: If the request fails
        ConnectionError: If there's a connection issue
    """
    if len(notifications) > 100:
        raise ValueError("Cannot send more than 100 notifications at once")
    
    headers = {
        "host": "exp.host",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
    
    payload = []
    for notification in notifications:
        message = {
            "to": notification["token"],
            "title": notification["title"],
            "body": notification["body"],
        }
        
        if notification.get("subtitle"):
            message["subtitle"] = notification["subtitle"]
        
        if notification.get("extra_data"):
            message["data"] = notification["extra_data"]
        
        payload.append(message)
    
    try:
        response = requests.post(
            EXPO_PUSH_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "errors" in result:
            print(f"Bulk push notification errors: {result['errors']}")
            raise HTTPError(f"Bulk push notification failed: {result['errors']}")
        
        if "data" in result:
            for i, ticket in enumerate(result["data"]):
                if ticket.get("status") == "error":
                    error_details = ticket.get("details", {})
                    token = notifications[i]["token"]
                    if error_details.get("error") == "DeviceNotRegistered":
                        print(f"Device not registered: {token}")
                        from services.supabase import superbase as supabase
                        try:
                            supabase.table('push_tokens').update({'active': False}).eq('token', token).execute()
                        except Exception as e:
                            print(f"Failed to update token status: {e}")
                    print(f"Push ticket error for {token}: {ticket}")
        
        return result
        
    except ConnectionError as exc:
        print(f"Connection error: {exc}")
        raise exc
    
    except HTTPError as exc:
        print(f"HTTP error: {exc}")
        raise exc