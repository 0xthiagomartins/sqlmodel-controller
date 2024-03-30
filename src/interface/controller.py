from typing import Any, Optional, List
from ...connection.sqlmodel.mysql import get_engine
from sqlalchemy.orm import Query
from sqlmodel import Session
import math
from werkzeug.exceptions import BadRequest
from .dao import Dao


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 25

class Page:
    def __init__(self, items, page, page_size, total):
        self.items = items
        self.previous_page = None
        self.next_page = None
        self.has_previous = page > 1
        if self.has_previous:
            self.previous_page = page - 1
        previous_items = (page - 1) * page_size
        self.has_next = previous_items + len(items) < total
        if self.has_next:
            self.next_page = page + 1
        self.total = total
        self.pages = int(math.ceil(total / float(page_size)))


def paginate(query, current_page: int, per_page: int, to_dict: bool = True):
    if not current_page:
        current_page = DEFAULT_PAGE
    current_page = int(current_page)

    if not per_page:
        per_page = DEFAULT_PER_PAGE
    per_page = int(per_page)

    if current_page < 0:
        raise BadRequest("Page needs to be >= 1")
    if per_page < 0:
        raise BadRequest("The page size needs to be >= 1")
    items = query.limit(per_page).offset((current_page - 1) * per_page).all()
    total = query.order_by(None).count()
    page_data = Page(items, current_page, per_page, total)
    if to_dict:
        return {
            "data_set": page_data.items,
            "current": current_page,
            "per_page": per_page,
            "total_pages": page_data.pages,
            "total_data": page_data.total,
            "previous": page_data.previous_page,
            "next": page_data.next_page,
        }
    else:
        return page_data

class Controller:
    engine = get_engine()
    model_class = None

    def _normalizer_dao_data(self, db_data_object, joins=None):
        if isinstance(db_data_object, list):
            return [obj.to_dict(joins=joins) for obj in db_data_object]
        if not db_data_object:
            return {}
        return db_data_object.to_dict(joins=joins)

    def _get_view(self, query: Query, joins: Optional[List[str]] = None, **kwargs):
        mode = kwargs.get("mode")
        page = kwargs.get("page")
        per_page = kwargs.get("per_page")
        match mode:
            case "paginated":
                view = paginate(query, current_page=page, per_page=per_page)
                view["data_set"] = self._normalizer_dao_data(
                    view.get("data_set"), joins=joins
                )
            case "all":
                view = self._normalizer_dao_data(query.all(), joins=joins)
            case _:
                view = []
        return view

    def get(
        self,
        by: str | List[str],
        value: Any | List[Any],
        joins: Optional[List[str]] = None,
    ):
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            dao_result = dao.get(by, value, joins=joins)
            if not dao_result:
                return {}
            view = self._normalizer_dao_data(dao_result, joins=joins)
            return view

    def list(
        self,
        filter: dict = {},
        order: dict = {},
        joins: list = [],
        **kwargs,
    ):
        with Session(self.engine) as session:
            query = Dao(session, self.model_class).list(filter, order, joins)
            return self._get_view(query=query, joins=joins, **kwargs)

    def create(self, data: dict) -> int:
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            return dao.create(data)

    def update(self, by: str | List[str], value: Any | List[Any], data: dict) -> int:
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            return dao.update(by, value, data)

    def upsert(
        self, by: Optional[str] = None, value: Optional[Any] = None, data: dict = {}
    ):
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            return dao.upsert(by, value, data)

    def archive(
        self,
        by: str | List[str],
        value: Any | List[Any],
    ):
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            dao.archive(by, value)

    def delete(
        self,
        by: str | List[str],
        value: Any | List[Any],
    ):
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            dao.delete(by, value)
