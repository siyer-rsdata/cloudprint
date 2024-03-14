from typing import Optional

from fastapi import APIRouter, Header
from fastapi.responses import Response

import logging

from backend.order_queue import OrderQueue
from backend.potlam_backend import update_status
from backend.schemas import PostPollRequest, PostPollResponse
from database.cloudprint_db import is_order_available_in_db, update_order_status_in_db
from libs.auth import Auth
from libs.constants import get_constant
from replace_template import create_print_file

router = APIRouter(prefix="/print")

auth = Auth()

queue = OrderQueue()

# Create a logger
logger = logging.getLogger(__name__)


@router.get("/{restaurant_code}")
def get_print_job(restaurant_code: str):

    auth_response = auth.is_authorized(authorization=None, restaurant_code=restaurant_code.lower())

    if auth_response.status:

        if queue.is_job_ready(restaurant_code):

            # Star CloudPrnt prints only one order at a time, and makes subsequent POST and GET calls
            # to fetch more orders if any in the queue.

            order = queue.pop_order(restaurant_code.lower())

            logger.info(f"Popped order from queue - restaurant_code:{order.restaurant_code} - uuid:{order.uuid} - "
                        f"cloud_print_id:{order.cloud_print_id} - order_id:{order.order_id} - "
                        f"date/time:{order.print_order.orderdate} {order.print_order.ordertime}")

            cp_file = create_print_file(
                uuid=order.uuid,
                logo_url=order.restaurant_details.logo_url,
                title=order.restaurant_details.name,
                datetime=order.print_order.orderdate + " " + order.print_order.ordertime,
                print_order=order.print_order,
                footer=order.restaurant_details.message
            )

            # Update status of this order in the POTLAM Backend
            update_status(cloud_print_id=order.cloud_print_id,
                          status=str(get_constant("CLOUDPRINT_STATUS_PRINT_IN_PROGRESS")))

            # Update status of this order to CLOUDPRINT_STATUS_PRINT_IN_PROGRESS in the database
            update_order_status_in_db(uuid=order.uuid, status=str(get_constant("CLOUDPRINT_STATUS_PRINT_IN_PROGRESS")))

            # Send this order, the CP file for printing in the response body.

            with open(cp_file, "rb") as f:
                content = f.read()

            return Response(status_code=200, media_type="text/vnd.star.markup", content=content)

        else:
            message = "No more orders in queue for " + restaurant_code
            return Response(status_code=200, media_type="text/plain", content=message)

    else:
        # CloudPrnt request needs to be authenticated, before any service calls can be placed.
        # Set status_code = 401, if authentication required.
        response = Response(status_code=auth_response.http_status, content=auth_response.to_json())
        response.headers["WWW-Authenticate"] = "Basic realm=\"Authentication Required\""

    return response


@router.post("/{restaurant_code}", response_model=PostPollResponse, status_code=200)
def post_poll(restaurant_code: str,
              request: PostPollRequest,
              Authorization: Optional[str] = Header(None)) -> PostPollResponse:
    auth_response = auth.is_authorized(Authorization, restaurant_code.lower())

    if auth_response.status:

        # Check whether there are orders available in the queue to be printed
        jobReady = queue.is_job_ready(restaurant_code)

        is_order_available_in_db(restaurant_code)

        # construct the PostPollResponse object.
        response = PostPollResponse(jobReady=str(jobReady).lower(),
                                    mediaTypes=["application/vnd.star.starprnt"],
                                    deleteMethod="GET"
                                    )

        logger.info(f"resp json: {response.to_json()}")

        response = Response(status_code=200, content=response.to_json())

    else:

        # CloudPrnt request needs to be authenticated, before any service calls can be placed.
        # Set status_code = 401, if authentication required.
        response = Response(status_code=auth_response.http_status, content=auth_response.to_json())
        response.headers["WWW-Authenticate"] = "Basic realm=\"Authentication Required\""

    return response


@router.delete("/{restaurant_code}")
def delete():
    return Response(status_code=200, content="Delete Call Response.")
