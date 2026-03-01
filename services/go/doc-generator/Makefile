.PHONY: build run clean

build:
	go build -o doc-generator ./cmd/main.go

run: build
	./doc-generator

clean:
	rm -f doc-generator

docker-build:
	docker build -t hivemind-doc-generator .

docker-run:
	docker run --rm \
		-v /home/welem/hivemind:/home/welem/hivemind \
		-v /var/run/docker.sock:/var/run/docker.sock \
		hivemind-doc-generator
