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
```sh
$ pip install sqlmodel-controller
---> 100%
Successfully installed sqlmodel-controller
```

## Configuration

1. Create a `.env` file in the project root directory with the following content:

```sh
DB_TYPE=mysql
DB_NAME=test
DB_USER=root
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=3306
```

This will use SQLite for development. You can change these settings to use MySQL or PostgreSQL if needed.

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

## Documentation

When adding new features or making changes, please update the relevant documentation in the `docs/` directory and add docstrings to your functions and classes.

## Troubleshooting

If you encounter any issues during setup or testing, please check the following:

1. Ensure your Python version is 3.8 or higher:
   ```
   python --version
   ```

2. Make sure all dependencies are installed correctly:
   ```
   pip list
   ```

3. Verify that your `.env` file is set up correctly and in the right location.

If you still face issues, please open an issue on the GitHub repository with details about your environment and the problem you're experiencing.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
