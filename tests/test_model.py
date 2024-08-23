import pytest
from datetime import datetime, date
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlmodel_controller.model import BaseModel, BaseArchived, BaseID


@pytest.mark.skip(reason="Not a test class")
class TestEnum(Enum):
    VALUE1 = 1
    VALUE2 = 2


@pytest.mark.skip(reason="Not a test class")
class TestBaseModel(BaseModel):
    test_field: str = Field(default="test")
    test_enum: TestEnum = Field(default=TestEnum.VALUE1)
    test_date: date = Field(default_factory=date.today)
    test_list: list = Field(default_factory=list)


def test_base_model_to_dict():
    model = TestBaseModel()
    model_dict = model.to_dict()

    assert "created_at" in model_dict
    assert "updated_at" in model_dict
    assert model_dict["test_field"] == "test"
    assert model_dict["test_enum"] == "VALUE1"
    assert isinstance(model_dict["test_date"], str)
    assert model_dict["test_list"] == []


def test_base_model_to_dict_with_joins():
    class NestedModel(BaseModel):
        nested_field: str = "nested"

    class TestModelWithNested(BaseModel):
        nested: NestedModel = Field(default_factory=NestedModel)
        nested_list: list[NestedModel] = Field(default_factory=lambda: [NestedModel()])

    model = TestModelWithNested()
    model_dict = model.to_dict(joins=["nested", "nested_list"])

    assert "nested" in model_dict
    assert isinstance(model_dict["nested"], dict)
    assert model_dict["nested"]["nested_field"] == "nested"
    assert isinstance(model_dict["nested_list"], list)
    assert len(model_dict["nested_list"]) == 1
    assert model_dict["nested_list"][0]["nested_field"] == "nested"


def test_base_archived():
    model = BaseArchived()
    assert hasattr(model, "archived")
    assert model.archived == False


def test_base_id():
    model = BaseID()
    assert hasattr(model, "id")
    assert model.id is None
    assert hasattr(model, "archived")
    assert model.archived == False


def test_inheritance():
    assert issubclass(BaseArchived, BaseModel)
    assert issubclass(BaseID, BaseArchived)
