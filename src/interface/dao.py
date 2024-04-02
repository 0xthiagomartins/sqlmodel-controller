from datetime import datetime
from pytz import utc
from typing import Any, Dict, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, not_
from werkzeug.exceptions import NotFound


def apply_nested_joins(relationship_attr, inner_joins):
    if inner_joins:
        if isinstance(inner_joins[0], list):
            return joinedload(relationship_attr).options(
                apply_nested_joins(
                    getattr(relationship_attr.mapper.class_, inner_joins[0][0]),
                    inner_joins[0][1:],
                )
            )
        else:
            return joinedload(relationship_attr).joinedload(
                getattr(relationship_attr.mapper.class_, inner_joins[0])
            )
    else:
        return joinedload(relationship_attr)


class Dao:
    """
    Data Access Object (DAO) class to interact with the database.
    """

    def __init__(self, db_session, model_class):
        self.db_session = db_session
        self.model_class = model_class
        self.now = datetime.utcnow().replace(tzinfo=utc)

    def _exclude_none_from_dict(self, data: dict) -> dict:
        return {k: v for k, v in data.items() if v is not None}

    def _populate_to_create(self, obj_data: Dict[str, Any]):
        self.model = self.model_class(**obj_data)
        self.model.created_at = self.now
        self.model.updated_at = self.now
        if hasattr(self.model, "archived"):
            self.model.archived = 0

        self.db_session.add(self.model)
        self.db_session.commit()
        return self.model.id

    def _populate_to_update(self, obj_db, obj_data: Dict[str, Any]):
        data_parsed = self._exclude_none_from_dict(obj_data)
        for field, value in data_parsed.items():
            setattr(obj_db, field, value)
        obj_db.updated_at = self.now
        self.db_session.commit()
        return obj_db

    def __apply_selector(self, query, by, value):
        if isinstance(by, list) and isinstance(value, list):
            if len(by) != len(value):
                raise ValueError("Length of 'by' and 'value' lists must be the same.")

            conditions = [getattr(self.model_class, b) == v for b, v in zip(by, value)]
            query = query.filter(and_(*conditions))
        else:
            query = query.filter(getattr(self.model_class, by) == value)
        return query

    def create(self, obj_data: Dict[str, Any]) -> int:
        try:
            return self._populate_to_create(obj_data)
        except SQLAlchemyError as e:
            if "1062" in str(e):
                duplicate_values = (
                    str(e)
                    .split("Duplicate entry")[1]
                    .split("for key")[0]
                    .strip()
                    .split("-")
                )
                column_details = (
                    str(e).split("for key")[1].split("\n")[0].strip().split(".")
                )
                columns = column_details[-1].split("_")[1:-1]
                message_parts = [
                    f"{col} = {val}" for col, val in zip(columns, duplicate_values)
                ]
                message = ", ".join(message_parts)
                raise Exception(
                    f"Error creating {self.model_class.__name__}. Duplicate entry: {message}."
                )
            raise Exception(
                f"{e} when creating {self.model_class.__name__} in the database."
            )

    def get(
        self,
        by: str | List[str],
        value: Any | List[Any],
        joins: Optional[List[str]] = None,
    ):
        query = self.db_session.query(self.model_class)
        query = self.__apply_joins(query, joins)
        query = self.__apply_selector(query, by, value)
        return query.first()

    def __apply_filter(self, query, filter):
        """
        Example:

        filter = {
            "col_numeric": {
                "gte": 0,
                "lte": 0,
            },
            "col_string":"value"
        }
        """
        conditions = []
        for key, value in filter.items():
            if isinstance(value, list):
                # Handle filtering for lists
                or_conditions = [getattr(self.model_class, key) == v for v in value]
                conditions.append(or_(*or_conditions))
            elif isinstance(value, dict):  # range filter
                range_filters = []
                if "eq" in value:
                    range_filters.append(getattr(self.model_class, key) == value["eq"])
                if "gte" in value:
                    range_filters.append(getattr(self.model_class, key) >= value["gte"])
                if "lte" in value:
                    range_filters.append(getattr(self.model_class, key) <= value["lte"])
                if "gt" in value:
                    range_filters.append(getattr(self.model_class, key) > value["gt"])
                if "lt" in value:
                    range_filters.append(getattr(self.model_class, key) < value["lt"])
                if "in" in value:
                    range_filters.append(
                        getattr(self.model_class, key).in_(value["in"])
                    )
                if "contains" in value:
                    range_filters.append(
                        getattr(self.model_class, key).contains(value["contains"])
                    )
                if "like" in value:
                    query = query.filter(
                        getattr(self.model_class, key).like(value["like"])
                    )
                if "not-eq" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key) == value["not-eq"])
                    )
                if "not-gte" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key) >= value["not-gte"])
                    )
                if "not-lte" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key) <= value["not-lte"])
                    )
                if "not-gt" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key) > value["not-gt"])
                    )
                if "not-lt" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key) < value["not-lt"])
                    )
                if "not-in" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key).in_(value["not-in"]))
                    )
                if "not-like" in value:
                    query = query.filter(
                        not_(getattr(self.model_class, key).like(value["not-like"]))
                    )
                if "not-contains" in value:
                    range_filters.append(
                        not_(getattr(self.model_class, key).contains(value["contains"]))
                    )
                if range_filters:
                    query = query.filter(and_(*range_filters))
            else:
                query = query.filter(getattr(self.model_class, key) == value)
        return query

    def __apply_ordernation(self, query, order):
        """
        Example:

        order: dict =  {
                "col1": "asc" # ascending
                "col2": "desc" # descending
            }
        """
        for column, direction in order.items():
            column = getattr(self.model_class, column)
            match direction:
                case "desc":
                    query = query.order_by(column.desc())
                case "asc":
                    query = query.order_by(column)
        return query

    def __apply_joins(self, query, joins):
        if joins:
            for join in joins:
                if isinstance(join, list):
                    # If join is a list, the first element is the join for the outer model
                    # and the remaining elements are the joins for the inner model
                    outer_join, *inner_joins = join
                    relationship_attr = getattr(self.model_class, outer_join, None)
                    if relationship_attr:
                        # Apply the join for the outer model and the joins for the inner model
                        query = query.options(
                            apply_nested_joins(relationship_attr, inner_joins)
                        )
                else:
                    # If join is a string, it's a join for the current model
                    relationship_attr = getattr(self.model_class, join, None)
                    if relationship_attr:
                        query = query.options(joinedload(relationship_attr))
        return query

    def list(
        self,
        filter: Dict = {},
        order: Dict = {},
        joins: Optional[List[str]] = None,
    ):
        query = self.db_session.query(self.model_class)
        query = self.__apply_filter(query, filter)
        query = self.__apply_joins(query, joins)
        query = self.__apply_ordernation(query, order)
        return query

    def update(self, by, value, obj_data: Dict[str, Any]) -> int:
        try:
            obj_db = self.get(by=by, value=value)
            updated_obj_db = self._populate_to_update(obj_db, obj_data)
            return updated_obj_db.id
        except SQLAlchemyError as e:
            if "1062" in str(e):
                duplicate_values = (
                    str(e)
                    .split("Duplicate entry")[1]
                    .split("for key")[0]
                    .strip()
                    .split("-")
                )
                column_details = (
                    str(e).split("for key")[1].split("\n")[0].strip().split(".")
                )
                columns = column_details[-1].split("_")[1:-1]
                message_parts = [
                    f"{col} = {val}" for col, val in zip(columns, duplicate_values)
                ]
                message = ", ".join(message_parts)

                raise Exception(
                    f"Error updating {self.model_class.__name__}. Duplicate entry: {message}."
                )
            raise Exception(
                f"{e} when updating the {self.model_class.__name__} in the database."
            )

    def upsert(self, by: Optional[str], value: Optional[Any], obj_data):
        try:
            obj_db = self.get(by, value)
            if not obj_db:
                return self.create(obj_data)
            else:
                _object_updated = self._populate_to_update(obj_db, obj_data)
                self.db_session.add(_object_updated)
                self.db_session.commit()
                return obj_db.id
        except SQLAlchemyError as e:
            if "1062" in str(e):
                duplicate_values = (
                    str(e)
                    .split("Duplicate entry")[1]
                    .split("for key")[0]
                    .strip()
                    .split("-")
                )
                column_details = (
                    str(e).split("for key")[1].split("\n")[0].strip().split(".")
                )
                columns = column_details[-1].split("_")[1:-1]
                message_parts = [
                    f"{col} = {val}" for col, val in zip(columns, duplicate_values)
                ]
                message = ", ".join(message_parts)

                raise Exception(
                    f"Upsert {self.model_class.__name__} error. Duplicate entry: {message}."
                )
            raise Exception(
                f"{e} to Upsert {self.model_class.__name__} in the database."
            )

    def archive(self, by: str, value: Any):
        try:
            query = self.db_session.query(self.model_class)

            query = apply_selector(query, self.model_class, by, value)

            records_to_archive = query.all()

            if not records_to_archive:
                raise NotFound(f"No {self.name} found with {by} = {value}")

            for record in records_to_archive:
                record.archived = 1

            self.db_session.commit()

        except SQLAlchemyError:
            raise Exception(
                f"Error archiving {self.name} records by {by} = {value} in the database."
            )

    def delete(self, by: str, value: Any):
        try:
            query = self.db_session.query(self.model_class)

            query = apply_selector(query, self.model_class, by, value)

            records_to_delete = query.all()

            if not records_to_delete:
                raise NotFound(
                    f"No {self.model_class.__name__} found with {by} = {value}"
                )

            for record in records_to_delete:
                self.db_session.delete(record)

            self.db_session.commit()
        except SQLAlchemyError:
            raise Exception(
                f"Error deleting {self.model_class.__name__} records by {by} = {value} in the database."
            )
