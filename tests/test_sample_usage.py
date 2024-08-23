import pytest
from datetime import date
from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool
from src.interface.controller import Controller
from src.model import BaseID


class PersonModel(BaseID, table=True):
    tax_id: str
    name: str
    birth_date: date
    nickname: str


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="controller")
def controller_fixture(engine):
    return Controller[PersonModel](engine=engine)


def test_create_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "thiago",
    }
    person_id = controller.create(data=person_data)
    assert person_id is not None


def test_upsert_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "thiago",
    }
    controller.create(data=person_data)

    updated_data = {
        "tax_id": "0123456789",
        "birth_date": date(2002, 1, 1),
    }
    person_id = controller.upsert(by="name", value="Thiago Martin", data=updated_data)
    assert person_id is not None

    updated_person = controller.get(by="id", value=person_id)
    assert updated_person["tax_id"] == "0123456789"
    assert updated_person["birth_date"] == "2002-01-01"


def test_update_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "thiago",
    }
    person_id = controller.create(data=person_data)

    controller.update(by="id", value=person_id, data={"name": "Thiago Martins"})
    updated_person = controller.get(by="id", value=person_id)
    assert updated_person["name"] == "Thiago Martins"


def test_get_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "thiago",
    }
    person_id = controller.create(data=person_data)

    person = controller.get(by=["id", "archived"], value=[person_id, False])
    assert person is not None
    assert person["name"] == "Thiago Martin"


def test_list_persons(controller):
    for i in range(5):
        controller.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {i}",
                "birth_date": date(1990, 1, 1),
                "nickname": f"person{i}",
            }
        )

    list_paginated = controller.list(mode="paginated")
    assert len(list_paginated["data_set"]) == 5

    list_all = controller.list(mode="all", order={"name": "asc"})
    assert len(list_all) == 5
    assert list_all[0]["name"] == "Person 0"


def test_archive_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "thiago",
    }
    person_id = controller.create(data=person_data)

    controller.archive(by=["id", "archived"], value=[person_id, False])
    archived_person = controller.get(by="id", value=person_id)
    assert archived_person["archived"] == True


def test_delete_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "thiago",
    }
    person_id = controller.create(data=person_data)

    controller.delete(by="id", value=person_id)
    deleted_person = controller.get(by="id", value=person_id)
    assert deleted_person == {}
