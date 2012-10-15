test:
	trial --rterrors tests.py

lint:
	pyflakes *.py
	pep8 --repeat *.py
