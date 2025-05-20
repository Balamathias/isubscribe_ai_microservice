from rest_framework.response import Response
from rest_framework import status as drf_status

class ResponseMixin:

    """
    Mixin to provide a standard response format for API endpoints.
    This mixin can be used in Django REST Framework views to ensure
    consistent response structure across the application.
    """

    def response(
        self, 
        data=None, 
        message="", 
        status_code=drf_status.HTTP_200_OK, 
        status=None,
        error=None,
        count=None,
        next=None,
        previous=None
    ):
        """
        Standard response format for API endpoints
        """
        response_data = {
            "message": message,
            "data": data,
            "status": status_code,
            "error": error
        }
        
        if count is not None:
            response_data["count"] = count
        if next is not None:
            response_data["next"] = next
        if previous is not None:
            response_data["previous"] = previous
            
        return Response(data=response_data, status= status or status_code)
    