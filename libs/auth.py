from fastapi import Header
from pydantic.dataclasses import dataclass

import datetime
import json

from libs.constants import get_constant


@dataclass
class AuthorizationResponse:
    status: bool
    http_status: int
    status_message: str

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Auth(object):
    _self = None
    auth_add_time: int
    auth_cutoff_times = {}

    def __new__(cls):
        # Create an instance of this class only if it does not already exist.
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self):
        print(f"Inside Auth class Init: AUTHORIZATION_ACTIVE_TIME: {get_constant("AUTHORIZATION_ACTIVE_TIME")}")
        self.auth_add_time = get_constant("AUTHORIZATION_ACTIVE_TIME")

    def is_authorized(self, authorization: Header, restaurant_code: str) -> AuthorizationResponse:

        # check if this restaurant has an authentication that is currently active.
        if self.is_active(restaurant_code):
            auth_response = AuthorizationResponse(
                status=True, http_status=200, status_message="Authenticated using active time token.")
        else:
            # Authorization header is not Empty, it is supplied by the printer.
            if authorization is not None:

                # Check if Authorization header supplied is what is expected.
                if authorization.endswith(get_constant("CLOUDPRINT_AUTHENTICATION")):
                    # if authorization.endswith("dGVzdFVzZXI6dGVzdFBhc3N3b3Jk"):

                    # Successfully Authenticated, updated the cutoff time token for any future authentications
                    self.update_auth_cutoff_time(restaurant_code)

                    auth_response = AuthorizationResponse(
                        status=True, http_status=200, status_message="Authenticated using authorization header.")

                else:
                    auth_response = AuthorizationResponse(
                        status=False, http_status=401, status_message="Authentication Failed. Invalid Credentials.")

            else:
                auth_response = AuthorizationResponse(
                    status=False, http_status=401, status_message="Authentication Required.")

        return auth_response

    def is_active(self, restaurant_code: str) -> bool:
        # Check if an authorization for this restaurant already exists in the dictionary
        if (self.get_auth_cutoff_time(restaurant_code) is not None and
                datetime.datetime.now() < self.get_auth_cutoff_time(restaurant_code)):
            return True
        else:
            return False

    def update_auth_cutoff_time(self, restaurant_code):
        current_time = datetime.datetime.now()

        # Add the number of seconds this authentication should be active for this printer
        future_cutoff_time = current_time + datetime.timedelta(seconds=int(self.auth_add_time))

        # Set it as the new authentication cutoff time for this restaurant printer
        self.auth_cutoff_times[restaurant_code] = future_cutoff_time
        # print(f"auth_cutoff_times:{self.auth_cutoff_times}")

    def get_auth_cutoff_time(self, restaurant_code: str):
        return self.auth_cutoff_times.get(restaurant_code)

