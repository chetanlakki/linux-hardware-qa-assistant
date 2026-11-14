import app
import llm_router


def choose_tool(question, last_tool):
    question = question.lower()

    if "ram" in question or "memory" in question:
        return "memory"

    if "cpu" in question or "processor" in question:
        return "cpu"

    if "disk" in question or "ssd" in question or "nvme" in question or "storage" in question:
        return "disk"

    if "gpu" in question or "graphics" in question or "video card" in question:
        return "gpu"

    if last_tool and (
        "what about it" in question
        or "what about that" in question
        or "tell me more" in question
        or "more details" in question
    ):
        return last_tool

    return "unknown"


def get_answer(tool_name):
    if tool_name == "cpu":
        cpu_info = app.get_cpu_info()
        model = cpu_info.get("Model name", "Not available")
        cores = cpu_info.get("Core(s) per socket", "Not available")
        logical_processors = cpu_info.get("CPU(s)", "Not available")

        return f"You have a {model} with {cores} physical cores and {logical_processors} logical processors."

    if tool_name == "memory":
        memory_info = app.get_memory_info()
        total = memory_info.get("total", "Not available")
        used = memory_info.get("used", "Not available")
        available = memory_info.get("available", "Not available")

        return f"You have {total} RAM. Currently {used} is used and {available} is available."

    if tool_name == "disk":
        disk_info = app.get_disk_info()

        if not disk_info:
            return "I could not find disk information."

        first_disk = disk_info[0]

        if "virtual disk" in first_disk["type"].lower():
            return "This WSL session shows virtual disks, so I cannot confirm the physical SSD type or whether it is NVMe."

        return (
            f"Linux can see a {first_disk['size']} {first_disk['type']}. "
            f"Model: {first_disk['model']}. NVMe: {first_disk['nvme']}."
        )

    if tool_name == "gpu":
        gpu_info = app.get_gpu_info()
        answer = f"GPU device: {gpu_info.get('device', 'Not available')}."

        if gpu_info.get("note"):
            answer += f" {gpu_info['note']}"

        return answer

    return "I could not understand which hardware information to check."
def main():
    print("Linux Hardware Assistant")
    print("Ask about CPU, RAM, disks, SSD/NVMe, or GPU.")
    print("Type 'exit' when you want to stop.")
    last_tool = None

    while True:
        question = input("\nYou: ").strip()

        if question.lower() == "exit" or question.lower() == "quit":
            print("Assistant: Goodbye.")
            break

        tool_name = choose_tool(question, last_tool)
        if tool_name == "unknown":
            print("Assistant: I can currently answer questions about CPU, RAM, disks, SSD/NVMe, and GPU.")
        else:
            try:
                model_tool = llm_router.choose_tool_with_llm(question, last_tool)

                if model_tool != "unknown":
                    tool_name = model_tool
            except Exception:
                pass

            try:
                answer = get_answer(tool_name)
            except (RuntimeError, ValueError) as error:
                answer = f"I could not retrieve {tool_name} information: {error}"

            print(f"Assistant: {answer}")
            last_tool = tool_name

if __name__ == "__main__":
    main()
