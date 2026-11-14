import json

from ollama import Client

import app


OLLAMA_URL = "http://172.24.208.1:11434"
client = Client(host=OLLAMA_URL)


def get_hardware_info(category: str) -> str:
    """Get current verified hardware information.

    Args:
        category: One of cpu, memory, disk, or gpu.
    """
    if category == "cpu":
        return json.dumps(app.get_cpu_info())

    if category == "memory":
        return json.dumps(app.get_memory_info())

    if category == "disk":
        return json.dumps(app.get_disk_info())

    if category == "gpu":
        return json.dumps(app.get_gpu_info())

    return json.dumps({"error": "Unknown hardware category."})


def ask_llm(question):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Linux hardware assistant. "
                "For every hardware question, call get_hardware_info first. "
                "Use only the returned tool data in your final answer. "
                "If data is unavailable, say you cannot determine it. "
                "Never guess hardware details."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    response = client.chat(
        model="qwen2.5:3b",
        messages=messages,
        tools=[get_hardware_info]
    )

    messages.append(response.message)

    if not response.message.tool_calls:
        return "The local model did not request hardware data. Please try asking a hardware question."

    for tool_call in response.message.tool_calls:
        category = tool_call.function.arguments.get("category")
        tool_result = get_hardware_info(category)

        messages.append({
            "role": "tool",
            "tool_name": "get_hardware_info",
            "content": tool_result
        })

    final_response = client.chat(
        model="qwen2.5:3b",
        messages=messages,
        tools=[get_hardware_info]
    )

    return final_response.message.content


def ask_llm_with_context(question, last_tool):
    if last_tool:
        question = f"Previous hardware topic: {last_tool}. User question: {question}"

    return ask_llm(question)



def choose_tool_with_llm(question, last_tool):
    previous_topic = last_tool or "none"

    messages = [
        {
            "role": "system",
            "content": (
                "You select the correct hardware tool. "
                "Call get_hardware_info for CPU, memory, disk, or GPU questions. "
                "For vague follow-up questions, use the previous hardware topic. "
                "Do not answer the user directly."
            )
        },
        {
            "role": "user",
            "content": (
                f"Previous hardware topic: {previous_topic}. "
                f"User question: {question}"
            )
        }
    ]

    response = client.chat(
        model="qwen2.5:3b",
        messages=messages,
        tools=[get_hardware_info]
    )

    if not response.message.tool_calls:
        return "unknown"

    category = response.message.tool_calls[0].function.arguments.get("category")

    if category in ["cpu", "memory", "disk", "gpu"]:
        return category

    return "unknown"
