PORTS = 5000:5000
VERSION = latest

IMAGE_NAME = icequeen1996/spongeapp
CONTAINER_NAME = spongeapp
CONTAINER_INSTANCE = default

build: 
	docker build -t $(IMAGE_NAME):$(VERSION)  .

push:	build
	echo "$(DOCKER_PASSWORD)" | docker login -u "$(DOCKER_USERNAME)" --password-stdin
	docker tag $(IMAGE_NAME) $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):$(VERSION)

shell:
	docker run --rm --name $(CONTAINER_NAME)-$(CONTAINER_INSTANCE) -i -t $(PORTS) $(VOLUMES) $(ENV) $(IMAGE_NAME):$(VERSION) /bin/bash

run:
	docker run --rm --name $(CONTAINER_NAME)-$(CONTAINER_INSTANCE) $(PORTS) $(VOLUMES) $(ENV) $(IMAGE_NAME):$(VERSION)

start:
	docker run --rm --name=$(CONTAINER_NAME)-$(CONTAINER_INSTANCE) -it -d -p $(PORTS) $(IMAGE_NAME):$(VERSION)

stop:
	docker stop $(CONTAINER_NAME)-$(CONTAINER_INSTANCE)

rm:
	docker rm $(CONTAINER_NAME)-$(CONTAINER_INSTANCE)

release:	build
	make push -e VERSION=$(VERSION)

travis:    push
