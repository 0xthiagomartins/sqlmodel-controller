# guide to deploy to pypi

1. python setup.py sdist bdist_wheel
2. python -m twine upload dist/*
