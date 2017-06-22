check: build
	docker run julia_buildbot_config_check

shell:
	docker run -ti julia_buildbot_config_check bash

build:
	docker build -t julia_buildbot_config_check .


