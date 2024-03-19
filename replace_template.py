import os.path

import logging

from backend.schemas import PrintOrderItem, Toppings, Topping, BodyItem
from database.cloudprint_db import delete_order_from_db
from libs.constants import get_constant
from libs.cputil import create_cp_order

# Create a logger
logger = logging.getLogger(__name__)


# Replace placeholders from the template file with this order's values
def replace_placeholders(template_file, values):
    with open(template_file, 'r') as f:
        template_content = f.read()

    # Iterate over the keys in the order_values dictionary
    for key, value in values.items():

        # Check if the value is an array - there is only one array,
        # which contains arrays of items and prices. if needed, we can add quantity as well later,
        # by adding a third item (quantity) to the inner array.

        if isinstance(value, list):
            # For arrays, iterate over each element and format them together
            # such that item and price appears in the same line
            formatted_item_row = f"[column: left: Item; right: Quantity]\n"
            for order_item in value:
                formatted_item_row += f"[column: left: {order_item[0]}; right: {order_item[1]}]\n"

            # Replace placeholder in the template with the formatted order item row
            template_content = template_content.replace(f"{{{key}}}", formatted_item_row)

        else:

            # Otherwise, placeholder is a string - directly replace placeholder with the value
            template_content = template_content.replace(f"{{{key}}}", str(value))

    return template_content


def extract_order_details(print_order: PrintOrderItem) -> list:
    order_item_rows = []

    # loop to get all the items, normal and common toppings from this order.
    for order in print_order.orderdetails:

        if hasattr(order, "item_name") and hasattr(order, "quantity"):

            # Order item
            order_item_rows.append([order.item_name, order.quantity])

            # Common Toppings
            if hasattr(order, "toppingsdetails") and hasattr(order.toppingsdetails, "commontoppings"):
                for toppings_details in order.toppingsdetails.commontoppings:
                    if (hasattr(toppings_details, "toppings") and
                            isinstance(toppings_details.toppings, Toppings) and
                            hasattr(toppings_details.toppings, "toppingname")):

                        if toppings_details.toppings.qty is not None:
                            order_item_rows.append([" - " + toppings_details.toppings.toppingname,
                                                    toppings_details.toppings.qty])
                        else:
                            order_item_rows.append([" - " + toppings_details.toppings.toppingname, 1])

            # Normal toppings
            if hasattr(order, "toppingsdetails") and hasattr(order.toppingsdetails, "normaltoppings"):
                for toppings_details in order.toppingsdetails.normaltoppings:
                    if (hasattr(toppings_details, "toppings") and
                            isinstance(toppings_details.toppings, Topping) and
                            hasattr(toppings_details.toppings, "toppingname")):

                        if toppings_details.toppings.qty is not None:
                            order_item_rows.append([" - " + toppings_details.toppings.toppingname,
                                                    toppings_details.toppings.qty])
                        else:
                            order_item_rows.append([" - " + toppings_details.toppings.toppingname, 1])

    return order_item_rows


def create_print_file(order: BodyItem) -> str:
    # Print order template file

    uuid = order.uuid
    logo_url = order.restaurant_details.logo_url
    title = order.restaurant_details.name
    restaurant_address = order.restaurant_details.address
    restaurant_phone = order.restaurant_details.phone
    datetime = order.print_order.orderdate + " " + order.print_order.ordertime
    print_order = order.print_order
    footer = order.restaurant_details.message

    order_items = extract_order_details(print_order)

    order_values = {
        "LOGO_IMAGE_URL": logo_url,
        "ORDER_RECEIPT_TITLE": title,
        "RESTAURANT_ADDRESS": restaurant_address,
        "RESTAURANT_PHONE_NO": restaurant_phone,
        "ORDER_ID": print_order.order_id,
        "ORDER_DATETIME": datetime,
        "ORDER_ITEM_ROWS": order_items,
        "FOOTER_MESSAGE": footer
    }

    template_file = get_constant("CLOUDPRINT_ORDER_PRINT_TEMPLATE")
    content = replace_placeholders(template_file, order_values)

    tmp_file = os.path.join(get_constant("CLOUDPRINT_ORDER_TEMP_FOLDER"), uuid + ".stm")
    cp_file = os.path.join(get_constant("CLOUDPRINT_ORDER_TEMP_FOLDER"), uuid + ".cp")

    # create star markup tmp file with the actual order content
    with open(tmp_file, 'w') as file:
        file.write(content)

    # create the cloud print understandable file based on the tmp file using the CPUtil
    cp_file = create_cp_order(tmp_file=tmp_file, cp_file=cp_file)

    return cp_file


def cleanup(restaurant_code: str, job_token: str):
    # Split the job_token by underscores and take the last element (uuid) which is used to create the temporary files.
    # job_token takes the form: <restaurant_code>_<order_id>_<cloud_print_id>_<uuid>

    uuid = job_token.split("_")[-1]
    order_id = job_token.split("_")[1]

    logger.info(f"Cleaning up by removing tmp files and Database entry. [{restaurant_code}] "
                f"[order.id:{order_id}] [uuid:{uuid}].")

    stm_file = os.path.join(get_constant("CLOUDPRINT_ORDER_TEMP_FOLDER"), uuid + ".stm")
    cp_file = os.path.join(get_constant("CLOUDPRINT_ORDER_TEMP_FOLDER"), uuid + ".cp")

    # Check if the stm file exists, if yes, remove file.
    if os.path.exists(stm_file):
        os.remove(stm_file)

    # Check if the cp file exists, if yes, remove file.
    if os.path.exists(cp_file):
        os.remove(cp_file)

    # Remove this order from the orders sqlite3 database table.
    delete_order_from_db(restaurant_code=restaurant_code, order_id=order_id)
