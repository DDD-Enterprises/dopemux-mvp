import time
import queue
import threading
from typing import List, Optional

# Simplified mock of current AIAgent and AgentSpawner logic
class MockAgent:
    def __init__(self):
        self.output_queue = queue.Queue()
        self.status = "running"

    def is_healthy(self):
        return True

    def send_command(self, command):
        # Simulate AI starting to respond after 0.5s
        def simulate_response():
            time.sleep(0.5)
            self.output_queue.put(("stdout", "Line 1: Thinking..."))
            time.sleep(0.2)
            self.output_queue.put(("stdout", "Line 2: 2+2=4"))
            time.sleep(0.2)
            self.output_queue.put(("stdout", "> ")) # Prompt

        threading.Thread(target=simulate_response).start()
        return True

    def get_output(self, timeout: float = 1.0) -> List[str]:
        output_lines = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                source, line = self.output_queue.get(timeout=0.1)
                output_lines.append(line)
            except queue.Empty:
                if output_lines:
                    # Got some output, can return
                    break
                continue

        return output_lines

class MockSpawner:
    def __init__(self, agent):
        self.agents = {"claude": agent}

    def send_to_agent(self, agent_type, command):
        agent = self.agents.get(agent_type)
        if not agent: return None

        success = agent.send_command(command)
        if not success: return None

        # Naive implementation from agent_spawner.py:396
        print(f"DEBUG: Starting naive sleep(2)...")
        start_time = time.time()
        time.sleep(2)  # Give AI time to respond

        output = agent.get_output(timeout=5.0)
        end_time = time.time()

        print(f"DEBUG: send_to_agent took {end_time - start_time:.2f} seconds")
        return output

def main():
    agent = MockAgent()
    spawner = MockSpawner(agent)

    print("Testing current naive implementation...")
    start = time.time()
    response = spawner.send_to_agent("claude", "What is 2+2?")
    total_time = time.time() - start

    print(f"Response received: {response}")
    print(f"Total time: {total_time:.2f} seconds")

    if any("> " in line for line in response):
        print("SUCCESS: Prompt detected in response.")
    else:
        print("FAILURE: Prompt NOT detected in response.")

if __name__ == "__main__":
    main()
