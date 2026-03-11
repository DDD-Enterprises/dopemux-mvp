import time
import queue
import threading
from typing import List, Optional
import sys
import os
import re

# Mock ResponseParser since it might depend on things we don't have
class MockResponseParser:
    ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    PROMPT_PATTERNS = [r'^>\s', r'^>\s*$', r'^>>>\s', r'^Claude:', r'^Gemini:', r'^\$\s']

    def _is_prompt(self, line: str) -> bool:
        for pattern in self.PROMPT_PATTERNS:
            if re.match(pattern, line):
                return True
        return False

# Mock AgentConfig, AgentType, AgentStatus
class AgentType:
    CLAUDE = "claude"

class AgentStatus:
    RUNNING = "running"

class AgentConfig:
    def __init__(self, agent_type, command, env):
        self.agent_type = agent_type
        self.command = command
        self.env = env

# Simplified AIAgent with the NEW logic from agent_spawner.py
class AIAgent:
    def __init__(self, config):
        self.config = config
        self.output_queue = queue.Queue()
        self.parser = MockResponseParser()
        self.status = AgentStatus.RUNNING

    def send_command(self, command: str) -> bool:
        def simulate_response():
            time.sleep(0.5)
            self.output_queue.put(("stdout", "Line 1: Thinking..."))
            time.sleep(0.2)
            self.output_queue.put(("stdout", "Line 2: 2+2=4"))
            time.sleep(0.2)
            self.output_queue.put(("stdout", "> ")) # Prompt

        threading.Thread(target=simulate_response).start()
        return True

    def is_healthy(self): return True

    def get_output(self, timeout: float = 1.0, wait_for_prompt: bool = False) -> list[str]:
        output_lines = []
        deadline = time.time() + timeout
        last_data_time = time.time()

        while time.time() < deadline:
            try:
                source, line = self.output_queue.get(timeout=0.1)
                output_lines.append(line)
                last_data_time = time.time()

                if wait_for_prompt:
                    clean_line = self.parser.ANSI_REGEX.sub("", line)
                    if self.parser._is_prompt(clean_line):
                        break
            except queue.Empty:
                if not wait_for_prompt and output_lines:
                    if time.time() - last_data_time > 0.2:
                        break
                continue

        return output_lines

class AgentSpawner:
    def __init__(self, agent):
        self.agents = {AgentType.CLAUDE: agent}

    def send_to_agent(self, agent_type, command):
        agent = self.agents.get(agent_type)
        if not agent or not agent.is_healthy(): return None
        if not agent.send_command(command): return None
        return agent.get_output(timeout=10.0, wait_for_prompt=True)

def main():
    config = AgentConfig(AgentType.CLAUDE, ["mock"], {})
    agent = AIAgent(config)
    spawner = AgentSpawner(agent)

    print("Testing improved implementation (Standalone Mock)...")
    start_time = time.time()
    response = spawner.send_to_agent(AgentType.CLAUDE, "What is 2+2?")
    end_time = time.time()

    print(f"Response received: {response}")
    print(f"send_to_agent took {end_time - start_time:.2f} seconds")

    if any("> " in line for line in response):
        print("SUCCESS: Prompt detected in response.")
    else:
        print("FAILURE: Prompt NOT detected in response.")

    duration = end_time - start_time
    if duration < 1.5:
        print(f"SUCCESS: Implementation took {duration:.2f}s, faster than fixed 2s sleep.")
    else:
        print(f"FAILURE: Implementation took {duration:.2f}s, NOT faster than 2s.")

if __name__ == "__main__":
    main()
