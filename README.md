# Linux Hardware Q&A Assistant

A local command-line chatbot that answers questions about Linux hardware using verified system data.

This project was built for Asama AI's Hardware Q&A Assistant problem.

## What it can answer

- What CPU do I have?
- How much RAM do I have?
- Is my SSD NVMe?
- What GPU do I have?
- Follow-up questions such as "What about it?" or "Tell me more."

## How it works

```text
User question
    |
    v
Local LLM selects one allowed hardware category
    |
    v
Python validates the category
    |
    v
Safe Linux command runs
    |
    v
Python creates an answer from verified data
```

The LLM can select only one of these categories:

```text
cpu, memory, disk, gpu
```

It cannot run shell commands.

## Project files

```text
app.py          Safe hardware inspection tools
chat.py         Interactive command-line chatbot
llm_router.py   Local LLM tool selector
requirements.txt Python dependency list
```

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install the local model

Install Ollama, then download the model:

```bash
ollama run qwen2.5:3b
```

This project uses a local model, so no OpenAI API key is required.

> **WSL note:** In this development setup, Ollama runs on Windows and Ubuntu reaches it through the Windows gateway address. If the address changes after a restart, update `OLLAMA_URL` near the top of `llm_router.py`. Run `ip route` in Ubuntu and use the address after `default via`.
### 4. Run the chatbot

```bash
python chat.py
```

Type `exit` to stop the chatbot.

## Safety design

The main safety rule is that the chatbot never runs a command written by the user or by the LLM.

Only these fixed commands are allowed:

```text
lscpu
free -h
lsblk -J -o NAME,SIZE,TYPE,MODEL,ROTA,TRAN
lspci
```

Additional safety choices:

- Commands are stored in an allow-list.
- Commands run with `shell=False`.
- Commands have a 5-second timeout.
- Unknown tool names are rejected.
- The LLM selects a category only.
- Python creates the final hardware answer from verified data.
- If data is unavailable, the chatbot says it cannot determine the answer.

For example, the chatbot does not claim a disk is not NVMe when WSL reports `NVMe: Unknown`.

## WSL limitations
## Key design decision

> I did not trust the LLM with system facts. It can choose a safe tool, but my application validates the tool, runs a fixed read-only command, and formats the answer from verified data.

This project was developed in Ubuntu through WSL2.

WSL can expose virtual hardware instead of the physical Windows hardware:

- Disk information may show `Virtual Disk`.
- The physical SSD type and NVMe status may be unavailable.
- GPU information may show a virtual Microsoft graphics device.
- Motherboard and RAM-slot details are not currently available.

The chatbot reports these limitations instead of guessing.

## Privacy

The local Qwen model runs through Ollama on the same laptop.

Hardware information is not sent to a cloud API. The only data provided to the model is the local question and the verified hardware result needed to answer it.

## Example conversation

```text
You: How much RAM do I have?
Assistant: You have 7.6Gi RAM. Currently 500Mi is used and 7.0Gi is available.

You: Is my SSD NVMe?
Assistant: This WSL session shows virtual disks, so I cannot confirm the physical SSD type or whether it is NVMe.

You: Delete all my files.
Assistant: I can currently answer questions about CPU, RAM, disks, SSD/NVMe, and GPU.
```

## Future improvements

- Add motherboard and RAM-slot inspection with a carefully scoped `dmidecode` permission rule.
- Detect more Linux distributions and missing commands.
- Replace the WSL-specific Ollama address with automatic configuration.
- Add automated tests for command parsing and failure cases.
