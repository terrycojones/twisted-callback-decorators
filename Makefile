test:
	trial --rterrors tests.py

lint:
	pyflakes *.py
	pep8 --repeat *.py

clean:
	rm -rf *.pyc *~ _trial_temp
