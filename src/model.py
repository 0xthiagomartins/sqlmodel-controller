from datetime import datetime, date, UTC
from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum

table = True


class BaseModel(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self, joins: Optional[list[str]] = None):
        data = {}
        for attr in self.__dict__:
            if not attr.startswith("_"):  # Exclude private attributes
                value = getattr(self, attr)
                if isinstance(value, Enum):
                    data[attr] = value.name  # Translate enum value to key
                elif isinstance(value, datetime) or isinstance(value, date):
                    data[attr] = value.isoformat()  # Convert datetime to string
                elif isinstance(value, list):
                    if all(isinstance(v, Enum) for v in value):
                        data[attr] = [
                            v.name for v in value
                        ]  # Translate list of enum values to list of keys
                    elif all(isinstance(v, BaseModel) for v in value):
                        if joins and attr in joins:
                            data[attr] = [
                                v.to_dict() for v in value
                            ]  # Convert list of BaseModel objects to list of dicts
                elif isinstance(value, BaseModel):
                    if joins and attr in joins:
                        data[attr] = value.to_dict()  # Convert BaseModel object to dict
                else:
                    data[attr] = value

        return data


class BaseArchived(BaseModel):
    archived: bool = Field(default=False)


class BaseID(BaseArchived):
    id: int = Field(primary_key=True, default=None)
