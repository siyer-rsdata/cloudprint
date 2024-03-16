from sqlmodel import create_engine, Session

import logging

from backend.schemas import CloudPrintOrderStatus
from libs.constants import get_constant

logger = logging.getLogger(__name__)

db_engine = create_engine(
    "sqlite:///cp_orders.db",
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=bool(get_constant("DB_ENGINE_ECHO"))  # Log generated SQL, set this to False on Production
)


def add_orders_to_db(db_orders: list[CloudPrintOrderStatus]):
    with Session(db_engine) as session:
        session.add_all(db_orders)
        session.commit()
        session.close()


# True if an order exists with status: CLOUDPRINT_STATUS_PRINT_PENDING for this restaurant
# in the database table; False otherwise
def is_order_available_in_db(restaurant_code: str) -> bool:

    # Check whether an order exists in the database that matches this restaurant code AND status =
    with Session(db_engine) as session:

        # Find whether there are any orders in the database from this restaurant
        # and status: CLOUDPRINT_STATUS_PRINT_PENDING
        count = session.query(CloudPrintOrderStatus
                              ).filter(
            CloudPrintOrderStatus.restaurant_code == restaurant_code.lower(),
            CloudPrintOrderStatus.status == str(get_constant("CLOUDPRINT_STATUS_PRINT_PENDING"))
        ).count()

        if count > 0:
            return True
        else:
            return False


def update_order_status_in_db(uuid: str, status: str):

    with (Session(db_engine) as session):
        session.query(CloudPrintOrderStatus
                      ).filter(CloudPrintOrderStatus.uuid == uuid).update({'status': status})

        session.commit()
        session.close()

        # logger.info(f"Updated status of order with ID: {uuid} to status: {status}")


def delete_order_from_db(restaurant_code: str, order_id: str):
    with (Session(db_engine) as session):
        session.query(CloudPrintOrderStatus
                      ).filter(CloudPrintOrderStatus.restaurant_code == restaurant_code.lower(),
                               CloudPrintOrderStatus.order_id == order_id).delete()

        session.commit()
        session.close()

        # logger.info(f"Deleted order [{restaurant_code}] [order_id:{order_id}] from the database.")


def is_order_in_db(restaurant_code: str, order_id: str) -> bool:
    with Session(db_engine) as session:

        count = session.query(CloudPrintOrderStatus
                              ).filter(CloudPrintOrderStatus.restaurant_code == restaurant_code.lower(),
                                       CloudPrintOrderStatus.order_id == order_id).count()

        if count > 0:
            # logger.info(f"Order {restaurant_code}:{order_id} found in the Database.")
            return True
        else:
            # logger.info(f"Order [{restaurant_code}] [order_id:{order_id}] Not found in the Database.")
            return False
