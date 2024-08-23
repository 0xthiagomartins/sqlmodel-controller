## Defining Models

Define your SQLModel models by inheriting from `BaseID`:

```python
from sqlmodel import Field
from sqlmodel_controller import BaseID


class PersonModel(BaseID, table=True):
    tax_id: str = Field(unique=True)
    name: str
    birth_date: date
    nickname: str
```

## Basic CRUD Operations

### Create

```python
from sqlmodel_controller import Controller

controller = Controller[PersonModel]
person_data = {
"tax_id": "123456789",
"name": "Thiago Martin",
"birth_date": date(1990, 1, 1),
"nickname": "0xthiagomartins",
}
person_id: int = controller.create(data=person_data)
```

### Read

#### Get by ID

```python
selector = {"by": "id", "value": person_id}
person: dict = controller.get(**selector)
```

#### Get by other field

```python
selector = {"by": "tax_id", "value": "123456789"}
person: dict = controller.get(**selector)
```

#### Get with multiple conditions

```python
selector = {"by": ["name", "archived"], "value": ["Thiago Martin", False]}
person: dict = controller.get(**selector)
```

### Update

```python
updated_data = {"name": "Thiago Martins"}
selector = {"by": "id", "value": person_id}
controller.update(**selector, data=updated_data)
```

### Delete

```python
selector = {"by": "id", "value": person_id}
controller.delete(**selector)
```

## Advanced Operations

### Upsert

```python
# It upsert based on constraints and primary keys (it auto detects if it's a new or existing record)
# Work for 1 PK or multiple PKs or constraints

upsert_data = {
    "tax_id": "123456789",
    "name": "Thiago Martins",
    "birth_date": date(1990, 1, 1),
    "nickname": "0xthiagomartins",
}
selector = {"by": "tax_id", "value": "123456789"}
person_id = controller.upsert(**selector, data=upsert_data)
```

### Archive

```python
selector = {"by": "id", "value": person_id}
controller.archive(**selector)
```

### Pagination

#### Get paginated results

```python
paginated_result = controller.list(mode="paginated", page=1, per_page=10)
```

#### Access paginated data

```python
items = paginated_result["data_set"]
current_page = paginated_result["current"]
per_page = paginated_result["per_page"]
total_pages = paginated_result["total_pages"]
total_data = paginated_result["total_data"]
previous = paginated_result["previous"]
next = paginated_result["next"]
```

### Filtering

#### Simple filter

```python
filtered_persons = controller.list(filter={
    "name": "John"
    }
)
```

#### Complex filter

```python
filtered_persons = controller.list(filter={
    "birth_date": {
        "gte": date(1990, 1, 1),
        "lt": date(2000, 1, 1)
        },
        "archived": False
    }
)
```

### Sorting

```python
sorted_persons = controller.list(order={
    "name": "asc",
    "birth_date": "desc"
    }
)
```

### Joins

#### Assuming a relationship between PersonModel and AddressModel

```python
person_with_address = controller.get(by="id", value=person_id, joins=["address"])
```

## Error Handling

The library raises exceptions for various error conditions. It's recommended to use try-except blocks to handle potential errors:

```python
from werkzeug.exceptions import NotFound


try:
    person = controller.get(by="id", value=999999)
except NotFound:
    print("Person not found")
except Exception as e:
    print(f"An error occurred: {str(e)}")
```

For more detailed information on specific methods and their parameters, please refer to the API documentation.