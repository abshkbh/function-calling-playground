import requests
import json
import grpc

from protos import api_pb2, api_pb2_grpc


def start_vm(
    vm_name: str, server_address: str = "localhost:50051"
) -> api_pb2.StartVMResponse:
    with grpc.insecure_channel(server_address) as channel:
        stub = api_pb2_grpc.VMManagementServiceStub(channel)
        request = api_pb2.StartVMRequest(vm_name=vm_name)

        try:
            response = stub.StartVM(request)
            return response
        except grpc.RpcError as e:
            raise RuntimeError(f"failed to start VM: {e}")


def execute_code_in_vm(
    code_server_addr: str,
    lang: str,
    files: dict[str, str],
    entry_point: str,
    dependencies: list[str],
    timeout: int,
):
    payload = {
        "lang": lang,
        "files": files,
        "entry_point": entry_point,
        "dependencies": dependencies,
        "timeout": timeout,
    }

    try:
        response = requests.post(f"{code_server_addr}/execute", json=payload)
        response.raise_for_status()
        result = response.json()
        return {
            "output": result.get("output", ""),
            "error": result.get("error", ""),
            "status": result.get("status", ""),
        }
    except requests.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Failed to decode API response")
