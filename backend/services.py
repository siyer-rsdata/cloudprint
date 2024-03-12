from pydantic import BaseModel
import json
from backend.schemas import PotlamOrderPrintStatus


class PotlamService(BaseModel):
    public_key: str = None

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class PotlamBulkUpdateOrderStatusService(PotlamService):
    order_list: list[PotlamOrderPrintStatus] = None


class PotlamUpdateOrderStatusService(PotlamService):
    cloud_print_id: str = None
    status: str = None


class PotlamOrdersListService(PotlamService):

    def __init__(self):
        super().__init__()
