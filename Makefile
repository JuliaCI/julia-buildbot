check: build
	docker run julia_buildbot_config_check

build:
	docker build -t julia_buildbot_config_check .


