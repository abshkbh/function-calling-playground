import os
import sys
import logging
import time
import argparse
import json

from openai import OpenAI
from dotenv import load_dotenv
from termcolor import colored
from api import start_vm, execute_code_in_vm
from google.protobuf.json_format import MessageToJson

LLM_MODEL = "claude-3-5-sonnet-latest"
FUNCTION_NAME_START_VM = "start_vm"
FUNCTION_NAME_EXECUTE_CODE_IN_VM = "execute_code_in_vm"

tools = [
    {
        "type": "function",
        "function": {
            "name": FUNCTION_NAME_START_VM,
            "description": "Helper function to start a VM using gRPC. Returns the IP address of the VM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vm_name": {
                        "type": "string",
                        "description": "The name of the VM to start.",
                    }
                },
                "required": ["vm_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": FUNCTION_NAME_EXECUTE_CODE_IN_VM,
            "description": "Execute code in a virtual machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lang": {
                        "type": "string",
                        "description": "The language of the code to be executed.",
                    },
                    "files": {
                        "type": "object",
                        "description": "A dictionary mapping file names to their contents.",
                        "properties": {
                            "main.py": {
                                "type": "string",
                                "description": "The main Python file content",
                            }
                        },
                    },
                    "entry_point": {
                        "type": "string",
                        "description": "The name of the file to be executed as the entry point.",
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of dependencies required for the code execution.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "The maximum time allowed for code execution in seconds.",
                    },
                    "code_server_addr": {
                        "type": "string",
                        "description": "The address of the code server running inside the VM.",
                    },
                },
                "required": ["lang", "files", "entry_point", "dependencies"],
            },
        },
    },
]


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }

    for message in messages:
        if message["role"] == "system":
            print(
                colored(
                    f"system: {message['content']}\n", role_to_color[message["role"]]
                )
            )
        elif message["role"] == "user":
            print(
                colored(f"user: {message['content']}\n", role_to_color[message["role"]])
            )
        elif message["role"] == "assistant" and message.get("function_call"):
            print(
                colored(
                    f"assistant: {message['function_call']}\n",
                    role_to_color[message["role"]],
                )
            )
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(
                colored(
                    f"assistant: {message['content']}\n", role_to_color[message["role"]]
                )
            )
        elif message["role"] == "function":
            print(
                colored(
                    f"function ({message['name']}): {message['content']}\n",
                    role_to_color[message["role"]],
                )
            )


def chat_completion_request(messages, tools=None, tool_choice=None, model=LLM_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def parse_arguments():
    parser = argparse.ArgumentParser(description="AI coding problem solver")
    parser.add_argument(
        "-p", "--prompt", type=str, required=True, help="Coding problem to solve"
    )
    return parser.parse_args()


def call_tool(
    tool_call_id: str, tool_function_name: str, tool_args: dict[any, any]
) -> dict[str, any]:
    print(f"Calling tool: {tool_function_name} args: {tool_args}")
    if tool_function_name == FUNCTION_NAME_START_VM:
        if "vm_name" not in tool_args:
            print(f"No vm_name in args for tool: {tool_function_name}")
            return {}

        response = start_vm(tool_args["vm_name"])
        print(f"{tool_function_name} response: {MessageToJson(response)}")
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_function_name,
            "content": MessageToJson(response),
        }
    elif tool_function_name == FUNCTION_NAME_EXECUTE_CODE_IN_VM:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_function_name,
            "content": "0",
        }
    else:
        print(f"Unknown tool function name: {tool_function_name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    load_dotenv(".env")
    llm_api_key = os.getenv("BRAINTRUST_PROXY_KEY")

    # Always use Braintrust cache. Useful for not losing money whiledebugging.
    client = OpenAI(
        base_url="https://api.braintrust.dev/v1/proxy",
        default_headers={"x-bt-use-cache": "always"},
        api_key=llm_api_key,
    )

    args = parse_arguments()
    system_prompt = os.getenv("SYSTEM_PROMPT")
    if not system_prompt:
        logger.error(f"No system prompt provided")
        sys.exit(1)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": args.prompt},
    ]

    while True:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=tools,
        )
        response_message = response.choices[0].message
        messages.append(response_message.to_dict())
        tool_calls = response_message.tool_calls
        pretty_print_conversation(messages)

        if response_message.role == "assistant" and not tool_calls:
            content = response_message.content
            if "?" not in content and "Would you like to" not in content:
                print(f"Nothing to do...ending")
                sys.exit(0)

            print("LLM is waiting for user input.")
            user_input = input("Your input: ")
            messages.append({"role": "user", "content": user_input})
            continue

        if not tool_calls:
            continue

        for tool_call in tool_calls:
            tool_call_id = tool_call.id
            tool_function_name = tool_call.function.name
            # TODO: Handle exception here.
            tool_call_result = call_tool(
                tool_call_id,
                tool_function_name,
                json.loads(tool_call.function.arguments),
            )
            messages.append(tool_call_result)
