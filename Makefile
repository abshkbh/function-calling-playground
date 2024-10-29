PROTOS_DIR := protos

.PHONY: protos
protos:
	python -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. $(PROTOS_DIR)/api.proto

.PHONY: clean
clean:
	rm -rf $(PROTOS_DIR)/*py $(PROTOS_DIR)/__pycache__

.PHONY: all
all: protos
