OUT_DIR := out
PROTOS_DIR := protos

.PHONY: protos
protos:
	mkdir -p $(OUT_DIR)
	python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. api.proto

.PHONY: clean
clean:
	rm -rf $(OUT_DIR)

.PHONY: all
all: protos
