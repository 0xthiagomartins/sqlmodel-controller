from typing import Any, Optional, List, TypeVar, Generic
from .connection import get_engine
from sqlmodel import Session, SQLModel
import math
from pydantic import BaseModel
from .dao import Dao
from sqlmodel import select, func


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 25


class Page(BaseModel):
    """
    Represents a page of data in a paginated result set.

    Attributes:
        data_set (List[Any]): The list of items on the current page.
        previous_page (Optional[int]): The number of the previous page, if it exists.
        next_page (Optional[int]): The number of the next page, if it exists.
        has_previous (bool): Indicates whether there is a previous page.
        has_next (bool): Indicates whether there is a next page.
        total (int): The total number of items across all pages.
        pages (int): The total number of pages.
    """

    data_set: List[Any]
    previous_page: Optional[int]
    next_page: Optional[int]
    has_previous: bool
    has_next: bool
    total: int
    pages: int

    @classmethod
    def create(cls, data_set: List[Any], page: int, page_size: int, total: int):
        """
        Creates a Page instance with calculated pagination information.

        Args:
            data_set (List[Any]): The list of items on the current page.
            page (int): The current page number.
            page_size (int): The number of items per page.
            total (int): The total number of items across all pages.

        Returns:
            Page: A Page instance with calculated pagination information.
        """
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
    """
    Paginates a query result.

    Args:
        query: The SQLAlchemy query to paginate.
        session (Session): The SQLAlchemy session.
        current_page (int): The current page number.
        per_page (int): The number of items per page.
        to_dict (bool, optional): Whether to return the result as a dictionary. Defaults to True.

    Returns:
        Union[dict, Page]: A dictionary or Page object containing the paginated results and metadata.

    Raises:
        ValueError: If current_page or per_page is less than 1.
    """
    if current_page < 1:
        raise ValueError("Page needs to be >= 1")
    if per_page < 1:
        raise ValueError("The page size needs to be >= 1")

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
    """
    A generic controller class for database operations on SQLModel classes.

    This class provides a high-level interface for common database operations
    such as creating, reading, updating, and deleting records.

    Attributes:
        engine: The SQLAlchemy engine to use for database connections.
    """

    def __init__(self, engine=None):
        """
        Initializes the Controller with a database engine.

        Args:
            engine (optional): The SQLAlchemy engine to use. If not provided, it will be obtained using get_engine().
        """
        self.engine = engine or get_engine()

    @property
    def model_class(self) -> type[ModelClass]:
        """
        Returns the SQLModel class associated with this controller.

        Returns:
            type[ModelClass]: The SQLModel class.
        """
        return self.__orig_class__.__args__[0]

    @property
    def Dao(self):
        return Dao[self.model_class]

    def _normalize_dao_data(self, db_data_object, joins=None):
        """
        Normalizes data returned from the DAO to a dictionary format.

        Args:
            db_data_object: The data object(s) returned from the DAO.
            joins (optional): A list of joined relationships to include in the result.

        Returns:
            Union[dict, List[dict]]: The normalized data as a dictionary or list of dictionaries.
        """
        if isinstance(db_data_object, list):
            return [obj.to_dict(joins=joins) for obj in db_data_object]
        return {} if not db_data_object else db_data_object.to_dict(joins=joins)

    def _get_view(self, query, session, joins: Optional[List[str]] = None, **kwargs):
        """
        Executes a query and returns the result in the specified format.

        Args:
            query: The SQLAlchemy query to execute.
            session: The SQLAlchemy session.
            joins (Optional[List[str]], optional): A list of joined relationships to include.
            **kwargs: Additional keyword arguments for pagination and result formatting.

        Returns:
            Union[dict, List[dict]]: The query result in the specified format.
        """
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
        """
        Retrieves a single record or list of records from the database.

        Args:
            by (str | List[str]): The column(s) to filter by.
            value (Any | List[Any]): The value(s) to filter with.
            joins (Optional[List[str]], optional): A list of joined relationships to include.

        Returns:
            Union[dict, List[dict]]: The retrieved record(s) as a dictionary or list of dictionaries.
        """
        with Session(self.engine) as session:
            dao = self.Dao(session, self.model_class)
            dao_result = dao.get(by, value, joins=joins)
            return self._normalize_dao_data(dao_result, joins=joins)

    def list(self, filter: dict = {}, order: dict = {}, joins: list = [], **kwargs):
        """
        Retrieves a list of records from the database based on the given filters and ordering.

        Args:
            filter (dict, optional): A dictionary of filters to apply to the query.
            order (dict, optional): A dictionary specifying the ordering of the results.
            joins (list, optional): A list of joined relationships to include.
            **kwargs: Additional keyword arguments for pagination and result formatting.

        Returns:
            Union[dict, List[dict]]: The query results in the specified format.
        """
        with Session(self.engine) as session:
            dao = self.Dao(session, self.model_class)
            query = dao.list(filter, order, joins)
            result = self._get_view(query=query, session=session, joins=joins, **kwargs)
            return result

    def create(self, data: dict, returns_object: bool = False) -> int | dict:
        """
        Creates a new record in the database.

        Args:
            data (dict): The data for the new record.

        Returns:
            int: The ID of the newly created record.
        """
        with Session(self.engine) as session:
            dao = self.Dao(session, self.model_class)
            obj_id = dao.create(data)
            if returns_object:
                obj = dao.get(by="id", value=obj_id)
                result = self._normalize_dao_data(obj)
            else:
                result = obj_id
        return result

    def update(self, by: str | List[str], value: Any | List[Any], data: dict) -> int:
        """
        Updates an existing record or records in the database.

        Args:
            by (str | List[str]): The column(s) to identify the record(s) to update.
            value (Any | List[Any]): The value(s) to identify the record(s) to update.
            data (dict): The new data to update the record(s) with.

        Returns:
            int: The number of records updated.
        """
        with Session(self.engine) as session:
            return Dao[self.model_class](session, self.model_class).update(
                by, value, data
            )

    def upsert(
        self, by: Optional[str] = None, value: Optional[Any] = None, data: dict = {}
    ):
        """
        Inserts a new record or updates an existing one if it already exists.

        Args:
            by (Optional[str], optional): The column to identify an existing record.
            value (Optional[Any], optional): The value to identify an existing record.
            data (dict, optional): The data for the new or updated record.

        Returns:
            int: The ID of the upserted record.
        """
        with Session(self.engine) as session:
            return Dao[self.model_class](session, self.model_class).upsert(
                by, value, data
            )

    def archive(self, by: str | List[str], value: Any | List[Any]):
        """
        Archives (soft deletes) a record or records in the database.

        Args:
            by (str | List[str]): The column(s) to identify the record(s) to archive.
            value (Any | List[Any]): The value(s) to identify the record(s) to archive.
        """
        with Session(self.engine) as session:
            Dao[self.model_class](session, self.model_class).archive(by, value)

    def delete(self, by: str | List[str], value: Any | List[Any]):
        """
        Deletes a record or records from the database.

        Args:
            by (str | List[str]): The column(s) to identify the record(s) to delete.
            value (Any | List[Any]): The value(s) to identify the record(s) to delete.
        """
        with Session(self.engine) as session:
            Dao[self.model_class](session, self.model_class).delete(by, value)
