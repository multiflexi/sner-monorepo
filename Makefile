.PHONY: db db-create-default db-create-test install-deps pylint test test-agent test-server


install-deps:
	apt-get install postgresql-all unzip nmap


venv:
	apt-get install python-virtualenv python3-virtualenv
	virtualenv -p python3 venv
	venv/bin/pip install -r requirements.txt


db: db-create-default
	#su -c 'bin/database-disconnect.sh sner' postgres
	bin/server db remove
	bin/server db init
	bin/server db initdata


db-create-default:
	su -c 'bin/database-create.sh sner' postgres
	mkdir -p /var/sner


db-create-test:
	su -c 'bin/database-create.sh sner_test' postgres
	mkdir -p /tmp/sner_test_var


pylint:
	python -m pylint sner tests


test: test-server test-agent

test-agent: test-server
	sh tests/agent/run_all.sh

test-server: db-create-test
	python -m pytest
