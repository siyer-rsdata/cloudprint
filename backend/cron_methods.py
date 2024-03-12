import uuid
import logging

from backend.potlam_backend import PotlamBackend, bulk_update_status
from backend.schemas import PotlamOrderPrintStatus, CloudPrintOrderStatus
from backend.services import PotlamOrdersListService
from libs.constants import get_constant
from database.cloudprint_db import is_order_in_db, delete_order_from_db, add_orders_to_db
from backend.order_queue import OrderQueue

queue = OrderQueue()

# Create a logger
logger = logging.getLogger(__name__)


async def cloudprint_orders():

    # Fetch Cloud Print Orders from the POTLAM Backend
    orders_list = PotlamOrdersListService()
    orders_list.public_key = get_constant("POTLAM_BACKEND_PUBLIC_KEY")

    potlam_backend = PotlamBackend(params=orders_list)
    orders = potlam_backend.fetch_cloudprint_orders()

    # TODO: Potentially, we can look into removing storing the order in the memory queue.
    #  this is probably not needed, and use only the database.

    # in_progress_orders = []
    print_pending_orders = []

    if orders is not None:

        logger.info(f"Adding orders to queues. Found: {len(orders.body)} new orders to print.")

        for order in orders.body:

            # Check whether PrintOrderItem object exists for this order, that is a print_order
            # object exists in the json response from the POTLAM backend for this order.
            # A valid order must contain PrintOrderItem object.

            if type(order.print_order).__name__ == "PrintOrderItem":

                order_exists_in_queue: bool = queue.is_order_in_queue(restaurant_code=order.restaurant_code,
                                                                      order=order)

                # Add this order to queue only if this order does not already exist in the queue.
                if not order_exists_in_queue:

                    # UUID is created, added to an order here, UUID is not available from the POTLAM backend.
                    #  In this case, re-use the existing UUID from the database for this order.
                    #  DO THIS UUID AFTER MAKING THE CHECK WHETHER ORDER EXISTS, AND DO IT ONLY IF IT DOESN'T
                    order.uuid = str(uuid.uuid4())

                    # Add this order to the queues for further processing including printing
                    queue.add_order(order)

                    # If this order already exists in the database, Delete it.
                    # This will be freshly added (with the new UUID) later.
                    if is_order_in_db(restaurant_code=order.restaurant_code, order_id=order.order_id):
                        delete_order_from_db(restaurant_code=order.restaurant_code, order_id=order.order_id)

                    # Update cloudprint status for this order, set it to in progress.
                    # status = PotlamOrderPrintStatus(
                    #    cloud_print_id=str(order.cloud_print_id),
                    #    status=str(get_constant("CLOUDPRINT_STATUS_PRINT_IN_PROGRESS")))

                    # add the status to list that will be used to update the status in the backend
                    # in_progress_orders.append(status)

                    # Add this order to the SQLite database table, that will be checked before sending
                    # the order to printer.
                    # TODO: Potentially also include order_date and order_time fields to the DB, to decide the sequence
                    #  in which the order to be printed - until then rely on order_id.
                    #  lowest order_id # to be printed first.
                    print_pending_orders.append(
                        CloudPrintOrderStatus(uuid=order.uuid,
                                              restaurant_code=order.restaurant_code.lower(),
                                              cloud_print_id=order.cloud_print_id,
                                              order_id=order.order_id,
                                              status=str(get_constant("CLOUDPRINT_STATUS_PRINT_PENDING")))
                    )

                else:
                    logger.info(
                        f"Order for {order.restaurant_code} order_id: {order.order_id} already exists in queue, skipped.")

            else:
                logger.info(f"Order skipped, contains empty print_order for "
                            f"[restaurant_code:{order.restaurant_code}] "
                            f"cloud_print_id:{order.cloud_print_id} order_id:{order.order_id}")

    else:
        logger.info("No new orders received from POTLAM backend for printing.")

    # if len(in_progress_orders) > 0:
        # Update status to: CLOUDPRINT_STATUS_PRINT_IN_PROGRESS for any valid orders.
        # bulk_update_status(in_progress_orders)

    if len(print_pending_orders) > 0:
        # Update status of orders in the database to: CLOUDPRINT_STATUS_PRINT_PENDING.
        add_orders_to_db(print_pending_orders)
