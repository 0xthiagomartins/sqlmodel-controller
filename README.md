# sqlmodel-controller

A Controller Interface for basic CRUD operations with SQLModel/SQLAlchemy

## Overview

The library supports advanced features like complex filtering, joins, and custom queries. Refer to the documentation for detailed examples and API reference.

sqlmodel-controller is a Python library that provides a simple and efficient way to perform CRUD (Create, Read, Update, Delete) operations using SQLModel and SQLAlchemy. It offers a high-level abstraction layer that simplifies database interactions in your applications.

## Features

- Easy-to-use Controller interface for CRUD operations
- Seamless integration with SQLModel and SQLAlchemy
- Flexible query building and filtering
- Support for pagination and sorting
- Asynchronous operations support
- Support for multiple database types (MySQL, SQLite, PostgreSQL)

# Development Guide

This guide will help you set up the project for development and testing.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/0xthiagomartins/sqlmodel-controller.git
   cd sqlmodel-controller
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the project dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root directory with the following content:
   ```
   DB_TYPE=sqlite
   DB_NAME=test
   ```
   This will use SQLite for development. You can change these settings to use MySQL or PostgreSQL if needed.

## Running Tests

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the tests using pytest:
   ```
   pytest
   ```

3. To run tests with coverage report:
   ```
   pytest --cov=src --cov-report=term-missing
   ```

## Development Workflow

1. Create a new branch for your feature or bug fix:
   ```
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and write tests for new functionality.

3. Run the tests to ensure everything is working:
   ```
   pytest
   ```

4. Commit your changes:
   ```
   git commit -am "Add your commit message here"
   ```

5. Push your changes to your fork:
   ```
   git push origin feature/your-feature-name
   ```

6. Create a pull request on GitHub.

## Code Style

This project follows PEP 8 style guide. You can use tools like `flake8` or `black` to ensure your code adheres to the style guide:

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
