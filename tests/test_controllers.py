import pytest
from datetime import date
from sqlmodel import SQLModel, create_engine, Field, Relationship
from sqlmodel.pool import StaticPool
from sqlmodel_controller import Controller, BaseID, BaseUUID


class AddressModel(BaseID, table=True):
    __tablename__ = "addresses"

    street: str
    city: str
    person_id: int = Field(foreign_key="persons.id")
    person: "PersonModel" = Relationship(back_populates="addresses")


class PersonModel(BaseID, table=True):
    __tablename__ = "persons"

    tax_id: str
    name: str
    birth_date: date
    nickname: str
    addresses: list[AddressModel] = Relationship(back_populates="person")


class UsersModel(BaseUUID, table=True):
    __tablename__ = "uuid_users"

    email: str


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def ctrl_person(engine):
    return Controller[PersonModel](engine=engine)


@pytest.fixture()
def ctrl_address(engine):
    return Controller[AddressModel](engine=engine)


@pytest.fixture()
def ctrl_user(engine):
    return Controller[UsersModel](engine=engine)


def test_create_person(ctrl_person):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = ctrl_person.create(data=person_data)
    assert person_id is not None


def test_upsert_person(ctrl_person):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    ctrl_person.create(data=person_data)

    updated_data = {
        "tax_id": "0123456789",
        "birth_date": date(2002, 1, 1),
    }
    person_id = ctrl_person.upsert(by="name", value="Thiago Martin", data=updated_data)
    assert person_id is not None

    updated_person = ctrl_person.get(by="id", value=person_id)
    assert updated_person["tax_id"] == "0123456789"
    assert updated_person["birth_date"] == "2002-01-01"


def test_update_person(ctrl_person):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = ctrl_person.create(data=person_data)

    ctrl_person.update(by="id", value=person_id, data={"name": "Thiago Martins"})
    updated_person = ctrl_person.get(by="id", value=person_id)
    assert updated_person["name"] == "Thiago Martins"


def test_get_person(ctrl_person):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = ctrl_person.create(data=person_data)

    person = ctrl_person.get(by=["id", "archived"], value=[person_id, False])
    assert person is not None
    assert person["name"] == "Thiago Martin"


def test_list_persons(ctrl_person):
    for i in range(5):
        ctrl_person.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {i}",
                "birth_date": date(1990, 1, 1),
                "nickname": f"person{i}",
            }
        )

    list_paginated = ctrl_person.list(mode="paginated")
    assert len(list_paginated["data_set"]) == 5

    list_all = ctrl_person.list(mode="all", order={"name": "asc"})
    assert len(list_all) == 5
    assert list_all[0]["name"] == "Person 0"


def test_archive_person(ctrl_person):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = ctrl_person.create(data=person_data)

    ctrl_person.archive(by=["id", "archived"], value=[person_id, False])
    archived_person = ctrl_person.get(by="id", value=person_id)
    assert archived_person["archived"] == True


def test_delete_person(ctrl_person):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = ctrl_person.create(data=person_data)

    ctrl_person.delete(by="id", value=person_id)
    deleted_person = ctrl_person.get(by="id", value=person_id)
    assert deleted_person == {}


def test_list_persons_with_order(ctrl_person):
    for i in range(5):
        ctrl_person.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {5-i}",
                "birth_date": date(1990, 1, 1),
                "nickname": f"person{i}",
            }
        )

    list_ordered = ctrl_person.list(mode="all", order={"name": "desc"})
    assert len(list_ordered) == 5
    assert list_ordered[0]["name"] == "Person 5"
    assert list_ordered[-1]["name"] == "Person 1"


def test_list_persons_with_filter(ctrl_person):
    for i in range(5):
        ctrl_person.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {i}",
                "birth_date": date(1990 + i, 1, 1),
                "nickname": f"person{i}",
            }
        )

    filtered_list = ctrl_person.list(filter={"birth_date": {"gte": date(1992, 1, 1)}})
    assert len(filtered_list) == 3
    assert all(person["birth_date"] >= "1992-01-01" for person in filtered_list)


def test_get_person_with_joins(ctrl_person, ctrl_address):
    person_data = {
        "tax_id": "123456789",
        "name": "Thiago Martin",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person_id = ctrl_person.create(data=person_data)

    address_data = {"street": "123 Main St", "city": "New York", "person_id": person_id}
    ctrl_address.create(data=address_data)

    person_with_address = ctrl_person.get(by="id", value=person_id, joins=["addresses"])
    assert "addresses" in person_with_address
    assert len(person_with_address["addresses"]) == 1
    assert person_with_address["addresses"][0]["street"] == "123 Main St"


def test_list_persons_with_complex_filter(ctrl_person):
    for i in range(10):
        ctrl_person.create(
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
    filtered_list = ctrl_person.list(filter=complex_filter)
    assert len(filtered_list) == 5
    assert all(1995 <= int(person["birth_date"][:4]) < 2000 for person in filtered_list)
    assert all("Person" in person["name"] for person in filtered_list)


def test_list_persons_with_pagination_and_order(ctrl_person):
    for i in range(20):
        ctrl_person.create(
            data={
                "tax_id": f"12345678{i}",
                "name": f"Person {20-i}",
                "birth_date": date(1990 + i, 1, 1),
                "nickname": f"person{i}",
            }
        )

    paginated_result = ctrl_person.list(
        mode="paginated", page=2, per_page=5, order={"name": "asc"}
    )
    assert len(paginated_result["data_set"]) == 5
    assert paginated_result["current"] == 2
    assert paginated_result["total_pages"] == 4
    assert paginated_result["data_set"][0]["name"] == "Person 14"
    assert paginated_result["data_set"][-1]["name"] == "Person 18"


def test_returns_object(ctrl_person):
    payload = {
        "tax_id": "123456789",
        "name": "Thiago Martins",
        "birth_date": date(1990, 1, 1),
        "nickname": "0xthiagomartins",
    }
    person: dict = ctrl_person.create(data=payload, returns_object=True)
    assert person.get("name") == payload.get("name")


def test_paginate_invalid_current_page(ctrl_person):
    with pytest.raises(ValueError) as exc_info:
        ctrl_person.list(mode="paginated", page=0, per_page=10)
    assert str(exc_info.value) == "Page needs to be >= 1"


def test_paginate_invalid_per_page(ctrl_person):
    with pytest.raises(ValueError) as exc_info:
        ctrl_person.list(mode="paginated", page=1, per_page=0)
    assert str(exc_info.value) == "The page size needs to be >= 1"


def test_uuid(ctrl_user):
    user_data = {
        "email": "some_email@email.com",
    }
    user_id = ctrl_user.create(data=user_data)
    assert user_id is not None

    import uuid

    assert isinstance(uuid.UUID(str(user_id)), uuid.UUID)
