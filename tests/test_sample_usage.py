import pytest
from datetime import date
from sqlmodel import SQLModel, create_engine, Field, Relationship
from sqlmodel.pool import StaticPool
from sqlmodel_controller import Controller, BaseID


class AddressModel(BaseID, table=True):
    street: str
    city: str
    person_id: int = Field(foreign_key="personmodel.id")
    person: "PersonModel" = Relationship(back_populates="addresses")


class PersonModel(BaseID, table=True):
    tax_id: str
    name: str
    birth_date: date
    nickname: str
    addresses: list[AddressModel] = Relationship(back_populates="person")


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="controller")
def controller_fixture(engine):
    return Controller[PersonModel](engine=engine)


@pytest.fixture(name="address_controller")
def address_controller_fixture(engine):
    return Controller[AddressModel](engine=engine)


def test_create_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = controller.create(data=person_data)
    assert person_id is not None


def test_upsert_person(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
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
        "nickname": "0xthiagomartins",
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
        "nickname": "0xthiagomartins",
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
        "nickname": "0xthiagomartins",
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
        "nickname": "0xthiagomartins",
    }
    person_id = controller.create(data=person_data)

    controller.delete(by="id", value=person_id)
    deleted_person = controller.get(by="id", value=person_id)
    assert deleted_person == {}


def test_list_persons_with_order(controller):
    for i in range(5):
        controller.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {5-i}",
                "birth_date": date(1990, 1, 1),
                "nickname": f"person{i}",
            }
        )

    list_ordered = controller.list(mode="all", order={"name": "desc"})
    assert len(list_ordered) == 5
    assert list_ordered[0]["name"] == "Person 5"
    assert list_ordered[-1]["name"] == "Person 1"


def test_list_persons_with_filter(controller):
    for i in range(5):
        controller.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {i}",
                "birth_date": date(1990 + i, 1, 1),
                "nickname": f"person{i}",
            }
        )

    filtered_list = controller.list(filter={"birth_date": {"gte": date(1992, 1, 1)}})
    assert len(filtered_list) == 3
    assert all(person["birth_date"] >= "1992-01-01" for person in filtered_list)


def test_get_person_with_joins(controller, address_controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = controller.create(data=person_data)

    address_data = {"street": "123 Main St", "city": "New York", "person_id": person_id}
    address_controller.create(data=address_data)

    person_with_address = controller.get(by="id", value=person_id, joins=["addresses"])
    assert "addresses" in person_with_address
    assert len(person_with_address["addresses"]) == 1
    assert person_with_address["addresses"][0]["street"] == "123 Main St"


def test_list_persons_with_complex_filter(controller):
    for i in range(10):
        controller.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {i}",
                "birth_date": date(1990 + i, 1, 1),
                "nickname": f"person{i}",
            }
        )

    complex_filter = {
        "birth_date": {"gte": date(1995, 1, 1), "lt": date(2000, 1, 1)},
        "name": {"contains": "Person"},
    }
    filtered_list = controller.list(filter=complex_filter)
    assert len(filtered_list) == 5
    assert all(1995 <= int(person["birth_date"][:4]) < 2000 for person in filtered_list)
    assert all("Person" in person["name"] for person in filtered_list)


def test_list_persons_with_pagination_and_order(controller):
    for i in range(20):
        controller.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {20-i}",
                "birth_date": date(1990 + i, 1, 1),
                "nickname": f"person{i}",
            }
        )

    paginated_result = controller.list(
        mode="paginated", page=2, per_page=5, order={"name": "asc"}
    )
    assert len(paginated_result["data_set"]) == 5
    assert paginated_result["current"] == 2
    assert paginated_result["total_pages"] == 4
    assert paginated_result["data_set"][0]["name"] == "Person 14"
    assert paginated_result["data_set"][-1]["name"] == "Person 18"


def test_returns_object(controller):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martins",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = controller.create(data=person_data, returns_object=True)
    print(person_id)
    assert person_id.get("name") == "Thiago Martins"
