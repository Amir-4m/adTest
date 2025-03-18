from rest_framework.views import exception_handler
from rest_framework import status


def extract_first_error(errors):
    """
    Recursively extract the first field and error message from a nested error dictionary.
    """
    if isinstance(errors, dict):
        # If the current level is a dictionary, iterate over its items
        for field, error in errors.items():
            if isinstance(error, list):
                # If the error is a list, return the first item in the list
                return field, error[0]
            elif isinstance(error, dict):
                # If the error is a nested dictionary, recurse
                nested_field, nested_error = extract_first_error(error)
                return f"{field}.{nested_field}", nested_error
    elif isinstance(errors, list) and len(errors) > 0:
        # Handle case where the top-level is a list of errors
        return "", errors[0]
    return "", "Unknown error"


def custom_exception_handler(exc, context):
    # Get the standard response from DRF's built-in handler
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'status_code': response.status_code,
            'error': True,
            'message': '',
            'errors': {}
        }

        # Handle specific cases
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                # For single error messages
                custom_response['message'] = response.data['detail']
            else:
                # For validation errors with multiple fields
                custom_response['message'] = 'Validation errors occurred'
                custom_response['errors'] = response.data

                # Extract the first field name and error message, including nested fields
                first_field, first_error = extract_first_error(response.data)
                custom_response['message'] = f"{first_field}, {first_error}"

        # For 400 errors (bad request)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response['message'] = custom_response['message'] or 'Bad request'

        response.data = custom_response

    return response
