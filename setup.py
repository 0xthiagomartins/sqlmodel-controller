from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sqlmodel-controller",
    version="0.1.0",
    author="Thiago Martins",
    author_email="martins@dmail.ai",
    description="A Controller Interface for basic CRUD operations with SQLModel/SQLAlchemy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0xthiagomartins/sqlmodel-controller",
    packages=find_packages(where="sqlmodel_controller"),
    package_dir={"": "sqlmodel_controller"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sqlmodel",
        "sqlalchemy",
        "pydantic",
        "mysql-connector-python",
        "pg8000",
        "pytest",
        "pytest-cov",
    ],
)