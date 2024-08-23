from typing import Any, Optional, List, TypeVar, Generic
from .connection import get_engine
from sqlalchemy.orm import Query
from sqlmodel import Session, SQLModel
import math
from werkzeug.exceptions import BadRequest
from pydantic import BaseModel
from .dao import Dao
from sqlmodel import select, func


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 25


class Page(BaseModel):
    data_set: List[Any]
    previous_page: Optional[int]
    next_page: Optional[int]
    has_previous: bool
    has_next: bool
    total: int
    pages: int

    @classmethod
    def create(cls, data_set: List[Any], page: int, page_size: int, total: int):
        return cls(
            data_set=data_set,
            previous_page=page - 1 if page > 1 else None,
            next_page=(
                page + 1 if (page - 1) * page_size + len(data_set) < total else None
            ),
            has_previous=page > 1,
            has_next=(page - 1) * page_size + len(data_set) < total,
            total=total,
            pages=int(math.ceil(total / float(page_size))),
        )


def paginate(
    query, session: Session, current_page: int, per_page: int, to_dict: bool = True
):
    if current_page < 1:
        raise BadRequest("Page needs to be >= 1")
    if per_page < 1:
        raise BadRequest("The page size needs to be >= 1")

    offset = (current_page - 1) * per_page
    data_set = session.exec(query.offset(offset).limit(per_page)).all()
    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    page_data = Page.create(data_set, current_page, per_page, total)

    if to_dict:
        return {
            "data_set": page_data.data_set,
            "current": current_page,
            "per_page": per_page,
            "total_pages": page_data.pages,
            "total_data": page_data.total,
            "previous": page_data.previous_page,
            "next": page_data.next_page,
        }
    return page_data


ModelClass = TypeVar("ModelClass", bound=SQLModel)


class Controller(Generic[ModelClass]):
    def __init__(self, engine=None):
        self.engine = engine or get_engine()

    @property
    def model_class(self) -> type[ModelClass]:
        return self.__orig_class__.__args__[0]

    def _normalize_dao_data(self, db_data_object, joins=None):
        if isinstance(db_data_object, list):
            return [obj.to_dict(joins=joins) for obj in db_data_object]
        return {} if not db_data_object else db_data_object.to_dict(joins=joins)

    def _get_view(self, query, session, joins: Optional[List[str]] = None, **kwargs):
        mode = kwargs.get("mode", "all")
        if mode == "paginated":
            view = paginate(
                query,
                session=session,
                current_page=kwargs.get("page", DEFAULT_PAGE),
                per_page=kwargs.get("per_page", DEFAULT_PER_PAGE),
            )
            view["data_set"] = self._normalize_dao_data(
                view.get("data_set"), joins=joins
            )
        elif mode == "all":
            view = self._normalize_dao_data(session.exec(query).all(), joins=joins)
        else:
            view = []
        return view

    def get(
        self,
        by: str | List[str],
        value: Any | List[Any],
        joins: Optional[List[str]] = None,
    ):
        with Session(self.engine) as session:
            dao = Dao[self.model_class](session, self.model_class)
            dao_result = dao.get(by, value, joins=joins)
            return self._normalize_dao_data(dao_result, joins=joins)

    def list(self, filter: dict = {}, order: dict = {}, joins: list = [], **kwargs):
        with Session(self.engine) as session:
            dao = Dao[self.model_class](session, self.model_class)
            query = dao.list(filter, order, joins)
            result = self._get_view(query=query, session=session, joins=joins, **kwargs)
            return result

    def create(self, data: dict) -> int:
        with Session(self.engine) as session:
            return Dao[self.model_class](session, self.model_class).create(data)

    def update(self, by: str | List[str], value: Any | List[Any], data: dict) -> int:
        with Session(self.engine) as session:
            return Dao[self.model_class](session, self.model_class).update(
                by, value, data
            )

    def upsert(
        self, by: Optional[str] = None, value: Optional[Any] = None, data: dict = {}
    ):
        with Session(self.engine) as session:
            return Dao[self.model_class](session, self.model_class).upsert(
                by, value, data
            )

    def archive(self, by: str | List[str], value: Any | List[Any]):
        with Session(self.engine) as session:
            Dao[self.model_class](session, self.model_class).archive(by, value)

    def delete(self, by: str | List[str], value: Any | List[Any]):
        with Session(self.engine) as session:
            Dao[self.model_class](session, self.model_class).delete(by, value)