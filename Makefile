REQUIREMENTS_FILE=requirements.txt
REQUIREMENTS_OUT=requirements.txt.log
SETUP_OUT=*.egg-info


all: setup requirements

requirements: $(REQUIREMENTS_OUT)

$(REQUIREMENTS_OUT): $(REQUIREMENTS_FILE)
	pip install -r $(REQUIREMENTS_FILE) | tee -a $(REQUIREMENTS_OUT)

setup: virtualenv $(SETUP_OUT)

$(SETUP_OUT): setup.py setup.cfg
	python setup.py develop
	touch $(SETUP_OUT)

clean:
	find . -name "*.py[oc]" -delete
	find . -name "__pycache__" -delete
	rm $(REQUIREMENTS_OUT)

test: setup requirements
	nosetests

virtualenv:
ifndef VIRTUAL_ENV
	$(error No VIRTUAL_ENV defined)
endif


## Develop:

INI_FILE=development.ini

develop: setup requirements
	screen -c develop.screenrc

serve: setup requirements
	pserve --reload $(INI_FILE)

shell: setup requirements
	pshell $(INI_FILE)
