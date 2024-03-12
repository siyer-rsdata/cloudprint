from __future__ import annotations
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from typing import List, Optional, Union

import json


'''
Below schemas are to support Star Cloud Printer HTTP Methods
See Star provided Documentation at the link below.

HTTP POST Server Polling Request:
https://star-m.jp/products/s_print/sdk/StarCloudPRNT/manual/en/protocol-reference/http-method-reference/server-polling-post/json-request.html

HTTP POST Server Polling Response:
https://star-m.jp/products/s_print/sdk/StarCloudPRNT/manual/en/protocol-reference/http-method-reference/server-polling-post/json-response.html

'''


class PostPollRequest(BaseModel):
    status: Optional[str] = None
    printerMAC: Optional[str] = None
    uniqueID: Optional[str] = None
    statusCode: str
    jobToken: Optional[str] = None
    printingInProgress: Optional[bool] = None
    clientAction: Optional[list] = None
    barcodeReader: Optional[list] = None
    keyboard: Optional[list] = None
    display: Optional[list] = None


@dataclass
class PostPollResponse:
    jobReady: Optional[str] = None
    mediaTypes: Optional[list] = None
    jobToken: Optional[str] = None
    deleteMethod: Optional[str] = None
    clientAction: Optional[list] = None
    claimBarcodeReader: Optional[bool] = None
    claimKeyboard: Optional[list] = None
    display: Optional[list] = None
    jobGetUrl: Optional[str] = None
    jobConfirmationUrl: Optional[str] = None

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class PotlamOrderPrintStatus:
    cloud_print_id: Optional[str] = None
    status: Optional[str] = None


# Cloud Print Orders List mapped to the below Pydantic class models
# Serialize and Deserialize json response returned by the POTLAM Backend Service.
#
# pydantic model of the json response generated from - https://jsontopydantic.com/
# perform the below two changes to the generated pydantic data model
# [1] Change the root model class to: CloudPrintOrdersModel
# [2] add - uuid: Optional[str] = None as the first element to class: BodyItem
# Do not make any other changes to the model and copy it below as-is.

class RestaurantDetails(BaseModel):
    name: str
    logo_url: Optional[str] = None
    address: str
    phone: str
    website: str
    message: str


class Toppings(BaseModel):
    topping_id: str
    toppingname: str
    qty: str
    toppingprice: str


class Commontopping(BaseModel):
    commoncategoryname: str
    toppings: Toppings


class Topping(BaseModel):
    topping_id: str
    toppingname: str
    qty: str
    toppingprice: str


class Normaltopping(BaseModel):
    normalcategoryname: str
    toppings: Union[List, Topping]


class Toppingsdetail(BaseModel):
    commontoppings: List[Union[List, Commontopping]]
    normaltoppings: List[Union[List, Normaltopping]]


class Orderdetail(BaseModel):
    order_id: str
    orderdetails_id: str
    itemid: str
    item_name: str
    item_image: str
    quantity: str
    toppingsdetails: Union[List, Toppingsdetail]


class PrintOrderItem(BaseModel):
    order_id: str
    orderdate: str
    ordertime: str
    orderstatus: str
    delivery: str
    pickup: str
    billingfirstname: str
    billinglastname: str
    billingaddress: str
    billingcity: str
    billingstate: str
    billingzipcode: str
    upcharge: Optional[str]
    upchargetransaction_id: Optional[str]
    refund: str
    refundtransaction_id: str
    order_cancelled: str
    cancelled_trancation_id: str
    subtotal: str
    tax: str
    tips: str
    delivery_charge: str
    discount: str
    upchargeamount: Optional[str]
    refundamount: str
    total: str
    orderdetails: List[Orderdetail]
    deliveryfirstname: Optional[str] = None
    deliverylastname: Optional[str] = None
    deliveryaddress: Optional[str] = None
    deliverycity: Optional[str] = None
    deliveryzipcode: Optional[str] = None


class BodyItem(BaseModel):
    uuid: Optional[str] = None
    cloud_print_id: str
    order_id: str
    restaurant_details: RestaurantDetails
    restaurant_code: str
    print_order: Union[str, PrintOrderItem]


class CloudPrintOrdersModel(BaseModel):
    status: int
    message: str
    body: List[BodyItem]


# Database table schema to track the print status of each order.
# This is also saved in memory but may not be long lived as it may be lost due to
# an application shutdown, termination, system shutdown etc. Hence, persisting the
# orders also in the database.
class CloudPrintOrderStatus(SQLModel, table=True):
    uuid: str = Field(primary_key=True, default=None)
    restaurant_code: str | None
    cloud_print_id: str | None
    order_id: str | None
    status: str | None
