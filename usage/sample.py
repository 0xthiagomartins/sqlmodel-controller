from sqlmodel import Field
from datetime import date
from typing import Optional
from src.model import BaseID, table
from src.interface import Controller


class PersonModel(BaseID, table=table):
    __tablename__ = "persons"

    tax_id: str
    name: str = Field(max_length=100)
    birth_date: Optional[date]
    nickname: str = Field(max_length=100)


if __name__ == "__main__":
    controller = Controller[PersonModel]()
    person_id = controller.create(
        data={
            "tax_id": "123456789",
            "name": "Thiago Martin",
            "birth_date": date(1990, 1, 1),
            "nickname": "thiago",
        }
    )
    person_id = controller.upsert(
        by="name",
        value="Thiago Martin",
        data={
            "tax_id": "0123456789",
            "birth_date": date(2002, 1, 1),
        },
    )
    controller.update(by="id", value=person_id, data={"name": "Thiago Martins"})
    person = controller.get(by=["id", "archived"], value=[person_id, False])
    list_paginated = controller.list(
        mode="paginated",
    )
    list_all = controller.list(
        mode="all",
        order={"name": "asc"},
    )
    controller.archive(by=["id", "archive"], value=[person_id, False])
    controller.delete(by="id", value=person_id)
