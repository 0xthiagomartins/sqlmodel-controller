## Setup Engine

To set up the database engine, you need to configure the following environment variables:
- `DB_TYPE` - sqlite, mysql, postgresql, mssql
- `DB_HOST` - hostname or ip address
- `DB_USER` - username
- `DB_PASSWORD` - password
- `DB_NAME` - database name
- `DB_PORT` - port number

you can either explicitly set your custom engine based on the following sample code:

```python
from sqlmodel import create_engine

def get_engine():
    config = get_db_config()
    if config["type"] == "mysql":
        db_uri = f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}"
    elif config["type"] == "sqlite":
        db_uri = f"sqlite:///{config['name']}.db"
    elif config["type"] == "postgres":
        db_uri = f"postgresql+pg8000://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}"
    else:
        raise ValueError(f"Unsupported database type: {config['type']}")
    return create_engine(db_uri)
```

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

## Initialize Controller

```python
from sqlmodel_controller import Controller

# if engine is not provided, it will use the default engine which is generated based on environment variables:

controller_with_specific_engice = Controller[PersonModel](engine=engine) 
controller = Controller[PersonModel]() # generate engine based on environment variables
```

## Basic CRUD Operations

### Create

```python
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
person_id: int = controller.upsert(**selector, data=upsert_data)
```

### Archive

```python
selector = {"by": "id", "value": person_id}
controller.archive(**selector)
```

### Listing

you can list all records from a table by calling the `list` method and setting the parameter `mode` to `"all"` or you can list the records in a paginated way by setting the parameter `mode` to `"paginated"` and providing the `page` and `per_page` parameters.

#### Get paginated results

```python
paginated_result: dict = controller.list(mode="paginated", page=1, per_page=10)
```

#### Access paginated data

```python
items: list[dict] = paginated_result["data_set"]
current_page: int = paginated_result["current"]
per_page: int = paginated_result["per_page"]
total_pages: int = paginated_result["total_pages"]
total_data: int = paginated_result["total_data"]
previous_page: int = paginated_result["previous"]
next_page: int = paginated_result["next"]
```

### Filtering

#### Simple filter

```python
filtered_persons = controller.list(filter={
    "name": "John"
    }
    mode="all"
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
    mode="all"
)
```

### Sorting

```python
sorted_persons = controller.list(order={
    "name": "asc",
    "birth_date": "desc"
    }
    mode="all"
)
```

### Joins

The joins only are applied for those fields whose relationship is defined in the model. If the field is not a relationship field, the join will not be applied. The join will be a list of objects if the relationship type is ManyToOne or ManyToMany (list). If the relationship type is OneToOne, the join will be a single object (dictionary). 

#### Assuming a relationship between PersonModel and AddressModel

```python
person_with_address = controller.get(
    by="id", 
    value=person_id, 
    joins=["address"]
    )
```

## Error Handling

The library raises exceptions for various error conditions. It's recommended to use try-except blocks to handle potential errors:

```python
from sqlalchemy.exc import NoResultFound


try:
    person = controller.get(by="id", value=999999)
except NoResultFound:
    print("Person not found")
except Exception as e:
    print(f"An error occurred: {str(e)}")
```

For more detailed information on specific methods and their parameters, please refer to the API documentation.