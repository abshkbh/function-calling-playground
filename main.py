import os
import grpc
import google.generativeai as genai

from dotenv import load_dotenv
from protos import api_pb2
from protos import api_pb2_grpc


def StartVM(vm_name: str, server_address: str = "localhost:50051") -> None:
    """
    Helper function to start a VM using gRPC.

    Args:
        vm_name (str): The name of the VM to start.
        server_address (str): The address of the gRPC server. Defaults to 'localhost:50051'.

    Returns:
        The response from the server (VMResponse).

    Raises:
        grpc.RpcError: If there's an error in the gRPC call.
    """
    # Create a gRPC channel
    with grpc.insecure_channel(server_address) as channel:
        # Create a stub (client)
        stub = api_pb2_grpc.VMManagementServiceStub(channel)

        # Create a VMRequest
        request = api_pb2.VMRequest(vm_name=vm_name)

        try:
            # Make the gRPC call
            response = stub.StartVM(request)
            return response
        except grpc.RpcError as e:
            raise RuntimeError(f"failed to start VM: {e}")


def configure_apis() -> None:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


if __name__ == "__main__":
    load_dotenv(".env")
    configure_apis()
    server_address = os.getenv("CHV_LAMBDA_SERVER_ADDRESS", "localhost:50051")

    try:
        response = StartVM("test", server_address)
        print(f"StartVM response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
    exit(0)
