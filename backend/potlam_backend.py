import json
import logging
import requests

from libs.constants import get_constant
from backend.schemas import CloudPrintOrdersModel
from backend.services import PotlamService, PotlamBulkUpdateOrderStatusService, PotlamUpdateOrderStatusService

logger = logging.getLogger(__name__)


class PotlamBackend:
    params: PotlamService

    def __init__(self, params: PotlamService = None):
        self.params = params

    def do_post(self, url) -> requests.Response:

        response: requests.Response

        try:

            # Make the POTLAM backend POST service call
            response = requests.post(url, data=self.params.to_json())

        except requests.exceptions.RequestException as e:
            logger.error("[backend:do_post] Error making POST request:", e)

        return response

    def update_order_status(self):

        # Create the service url for Print Status Update from the env constants
        service_url = get_constant("POTLAM_BACKEND_HOST") + get_constant("POTLAM_STATUS_UPDATE")

        response = self.do_post(service_url)

    def bulk_update_order_status(self):

        # Create the service url for Bulk Print Status Update from the env constants
        service_url = get_constant("POTLAM_BACKEND_HOST") + get_constant("POTLAM_MULTI_STATUS_UPDATE")

        response = self.do_post(service_url)

    def fetch_cloudprint_orders(self):

        # Create the service url from the env constants
        service_url = get_constant("POTLAM_BACKEND_HOST") + get_constant("POTLAM_PRINT_LIST")

        response = self.do_post(service_url)

        # Deserialize response into pydantic data model
        try:

            # response.text is empty if there are no more pending orders to print in POTLAM database.
            if len(response.text) > 0:
                orders = CloudPrintOrdersModel.parse_raw(response.text)

            else:
                orders = None

            return orders

        except Exception as e:
            logger.error(f"Error deserializing response into CloudPrintOrdersModel:", e)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


def bulk_update_status(in_progress_orders: list):
    # Bulk update status of orders in POTLAM Backend
    update_orders_status = PotlamBulkUpdateOrderStatusService(order_list=in_progress_orders)
    update_orders_status.public_key = get_constant("POTLAM_BACKEND_PUBLIC_KEY")

    potlam_backend = PotlamBackend(params=update_orders_status)

    potlam_backend.bulk_update_order_status()


def update_status(cloud_print_id: str, status: str):
    # Update status of a single order in the POTLAM Backend
    update_order_status = PotlamUpdateOrderStatusService(cloud_print_id=cloud_print_id, status=status)
    update_order_status.public_key = get_constant("POTLAM_BACKEND_PUBLIC_KEY")

    potlam_backend = PotlamBackend(params=update_order_status)

    potlam_backend.update_order_status()
