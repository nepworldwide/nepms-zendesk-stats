NAME   = hub.mnw.no/nepms-zendesk-stats
VERSION = $$(cat VERSION)
TAG    = $$(git log -1 --pretty=%h)
IMG    = ${NAME}:${VERSION}-${TAG}
LATEST = ${NAME}:latest

build:
	docker build -t ${IMG} .
	docker tag ${IMG} ${LATEST}

push:
	docker push ${NAME}

run:
	docker run ${NAME}