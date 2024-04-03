from typing import Any, Optional, List
from ...connection.sqlmodel.mysql import get_engine
from sqlalchemy.orm import Query
from sqlmodel import Session, SQLModel
import math
from werkzeug.exceptions import BadRequest
from .dao import Dao


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 25


class Page:
    def __init__(self, items, page, page_size, total):
        """
        Represents a page of items in a paginated result.

        Args:
            items: The list of items in the current page.
            page: The current page number.
            page_size: The number of items per page.
            total: The total number of items in the result.
        """
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
    """
    Paginates a SQLAlchemy query result.

    Args:
        query: The SQLAlchemy query to paginate.
        current_page: The current page number.
        per_page: The number of items per page.
        to_dict: Whether to convert the result to a dictionary.

    Returns:
        If `to_dict` is True, returns a dictionary with the paginated result.
        If `to_dict` is False, returns a `Page` object representing the paginated result.
    """
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


class Controller[ModelClass: SQLModel]:
    def __init__(self):
        """
        Initializes the controller.

        Args:
            model_class: The model class to use in the controller.
        """
        self.engine = get_engine()

    @property
    def model_class(self) -> ModelClass:
        return self.__orig_class__.__args__[0]

    def _normalizer_dao_data(self, db_data_object, joins=None):
        """
        Normalizes the data returned by the DAO.

        Args:
            db_data_object: The data returned by the DAO.
            joins: The list of joins to include in the normalization process.

        Returns:
            The normalized data.
        """
        if isinstance(db_data_object, list):
            return [obj.to_dict(joins=joins) for obj in db_data_object]
        if not db_data_object:
            return {}
        return db_data_object.to_dict(joins=joins)

    def _get_view(self, query: Query, joins: Optional[List[str]] = None, **kwargs):
        """
        Gets the view based on the query and parameters.

        Args:
            query: The SQLAlchemy query.
            joins: The list of joins to include in the view.
            kwargs: Additional parameters.

        Returns:
            The view data.
        """
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
        """
        Retrieves a single item from the database.

        Args:
            by: The field(s) to search by.
            value: The value(s) to search for.
            joins: The list of joins to include in the query.

        Returns:
            The retrieved item.
        """
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
        """
        Retrieves a list of items from the database.

        Args:
            filter: The filter criteria.
            order: The order criteria.
            joins: The list of joins to include in the query.
            kwargs: Additional parameters.

        Returns:
            The list of items.
        """
        with Session(self.engine) as session:
            query = Dao(session, self.model_class).list(filter, order, joins)
            return self._get_view(query=query, joins=joins, **kwargs)

    def create(self, data: dict) -> int:
        """
        Creates a new item in the database.

        Args:
            data: The data for the new item.

        Returns:
            The ID of the created item.
        """
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            return dao.create(data)

    def update(self, by: str | List[str], value: Any | List[Any], data: dict) -> int:
        """
        Updates an item in the database.

        Args:
            by: The field(s) to search by.
            value: The value(s) to search for.
            data: The updated data.

        Returns:
            The number of updated items.
        """
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            return dao.update(by, value, data)

    def upsert(
        self, by: Optional[str] = None, value: Optional[Any] = None, data: dict = {}
    ):
        """
        Upserts an item in the database.

        Args:
            by: The field to search by.
            value: The value to search for.
            data: The data for the item.

        Returns:
            The ID of the upserted item.
        """
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            return dao.upsert(by, value, data)

    def archive(
        self,
        by: str | List[str],
        value: Any | List[Any],
    ):
        """
        Archives an item in the database.

        Args:
            by: The field(s) to search by.
            value: The value(s) to search for.
        """
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            dao.archive(by, value)

    def delete(
        self,
        by: str | List[str],
        value: Any | List[Any],
    ):
        """
        Deletes an item from the database.

        Args:
            by: The field(s) to search by.
            value: The value(s) to search for.
        """
        with Session(self.engine) as session:
            dao = Dao(session, self.model_class)
            dao.delete(by, value)
