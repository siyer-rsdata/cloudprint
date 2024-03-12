from collections import deque
import logging

from backend.schemas import BodyItem

logger = logging.getLogger(__name__)


class OrderQueue:
    queues = {}

    _self = None

    def __new__(cls):
        # Create an instance of this class only if it does not already exist.
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def add_order(self, order: BodyItem):

        queue = self.queues.get(order.restaurant_code.lower())

        # TODO: Check whether an order with the same order_id, cloud_print_id and restaurant_code exists
        #  in the queue. Do NOT add the order if it already exists.
        #  There is a chance of duplicate orders in the queue IF the status of the orders is
        #  updated with a delay OR not updated.

        if queue is not None:
            queue.appendleft(order)
        else:
            queue = deque([order])

        # Add this order to the queue of this restaurant
        self.queues[order.restaurant_code.lower()] = queue

        logger.info(f"Order added to CloudPrint Queue for [restaurant_code:{order.restaurant_code}] "
                    f"cloud_print_id:{order.cloud_print_id} order_id:{order.order_id}")

    def get_orders(self, restaurant_code: str) -> deque:
        return self.queues.get(restaurant_code)

    def pop_order(self, restaurant_code: str) -> BodyItem:
        return self.queues.get(restaurant_code.lower()).pop()

    def length(self, restaurant_code: str) -> int:
        if self.queues.get(restaurant_code.lower()) is not None:
            return len(self.queues.get(restaurant_code.lower()))
        else:
            return 0

    # True if queue exists and length of queue is > 0 for this restaurant
    # False otherwise
    def is_job_ready(self, restaurant_code: str) -> bool:
        if (self.queues.get(restaurant_code.lower()) is not None
                and len(self.queues.get(restaurant_code.lower())) > 0):
            return True
        else:
            return False

    def is_order_in_queue(self, restaurant_code: str, order: BodyItem) -> bool:

        orders = self.get_orders(restaurant_code.lower())

        if orders is None or len(orders) == 0:
            return False
        else:

            for existing_order in orders:

                if existing_order.order_id == order.order_id:
                    return True

            return False
