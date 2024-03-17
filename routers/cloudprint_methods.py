from typing import Optional

from fastapi import APIRouter, Header, status
from fastapi.responses import Response

import logging

from backend.order_queue import OrderQueue
from backend.potlam_backend import update_status
from backend.schemas import PostPollRequest, PostPollResponse
from database.cloudprint_db import update_order_status_in_db, delete_order_from_db
from libs.auth import Auth
from libs.constants import get_constant
from replace_template import create_print_file, cleanup

router = APIRouter(prefix="/cloudprint")

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

            logger.info(f"Order popped from CloudPrint Queue [{order.restaurant_code}] [order_id:{order.order_id}] "
                        f"[cloudprint_id:{order.cloud_print_id}] "
                        f"[order date/time:{order.print_order.orderdate} {order.print_order.ordertime}]")

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

            logger.info(f"Printing order [{restaurant_code}] [order.id:{order.order_id}] "
                        f"[cloudprint_id:{order.cloud_print_id}]")
            logger.info(f"No of orders in queue for [{restaurant_code}]: [{queue.length(restaurant_code)}]")

            return Response(content, status_code=200, media_type="application/vnd.star.starprnt")

        else:
            message = "No more orders in queue for " + restaurant_code
            return Response(content=message, status_code=200, media_type="text/plain")

    else:
        # CloudPrnt request needs to be authenticated, before any service calls can be placed.
        # Set status_code = 401, if authentication required.
        response = Response(content=auth_response.to_json(), status_code=auth_response.http_status)
        response.headers["WWW-Authenticate"] = "Basic realm=\"Authentication Required\""

    return response


@router.post("/{restaurant_code}", response_model=PostPollResponse, status_code=status.HTTP_200_OK)
def post_poll(restaurant_code: str,
              request: PostPollRequest,
              Authorization: Optional[str] = Header(None)) -> PostPollResponse:
    auth_response = auth.is_authorized(Authorization, restaurant_code.lower())

    if auth_response.status:

        # Check whether there are orders available in the queue to be printed
        jobReady = queue.is_job_ready(restaurant_code)
        queue_len = queue.length(restaurant_code)

        # is_order_available_in_db(restaurant_code)

        # Create job token for the next order that will be popped,
        # token will have to be sent in the Post Poll response only if jobReady = true
        job_token = None
        if jobReady:
            job_token = queue.get_token_for_next_order(restaurant_code)

        # construct the PostPollResponse object.
        response = PostPollResponse(jobReady=str(jobReady).lower(),
                                    mediaTypes=["application/vnd.star.starprnt"],
                                    jobToken=job_token,
                                    deleteMethod="DELETE"
                                    )

        logger.info(f"No of orders in queue for [{restaurant_code}]: [{queue_len}]")

        response = Response(content=response.to_json(), status_code=status.HTTP_200_OK)

    else:

        # CloudPrnt request needs to be authenticated, before any service calls can be placed.
        # Set status_code = 401, if authentication required.
        response = Response(status_code=auth_response.http_status, content=auth_response.to_json())
        response.headers["WWW-Authenticate"] = "Basic realm=\"Authentication Required\""

    return response


@router.delete("/{restaurant_code}", status_code=status.HTTP_200_OK)
def delete(restaurant_code: str, jobToken: str):

    # Cleanup by removing stm and cp temporary files and delete the sqlite3 database table entry for this order.
    cleanup(restaurant_code, jobToken)

    # Return 200
    return Response(status_code=200, content="Success.")
