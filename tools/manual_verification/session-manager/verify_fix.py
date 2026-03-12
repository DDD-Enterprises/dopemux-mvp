import time
import threading
from typing import List
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "services/session-manager/src"))

from agent_spawner import AIAgent, AgentSpawner, AgentConfig, AgentType, AgentStatus

# Mock AIAgent to avoid subprocess and tmux
class MockRealAIAgent(AIAgent):
    def __init__(self, config):
        super().__init__(config)
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

    def is_healthy(self) -> bool:
        return True

def main():
    config = AgentConfig(
        agent_type=AgentType.DOPE_BRAINZ,
        command=["mock"],
        env={}
    )
    agent = MockRealAIAgent(config)
    spawner = AgentSpawner()
    spawner.agents[AgentType.DOPE_BRAINZ] = agent

    print("Testing improved implementation...")
    start_time = time.time()
    response = spawner.send_to_agent(AgentType.DOPE_BRAINZ, "What is 2+2?")
    end_time = time.time()

    print(f"Response received: {response}")
    print(f"send_to_agent took {end_time - start_time:.2f} seconds")

    if any("> " in line for line in response):
        print("SUCCESS: Prompt detected in response.")
    else:
        print("FAILURE: Prompt NOT detected in response.")

    if (end_time - start_time) < 1.5:
        print("SUCCESS: Implementation is faster than fixed 2s sleep.")
    else:
        print(f"FAILURE: Implementation took {end_time - start_time:.2f}s, which is not faster than 2s.")

if __name__ == "__main__":
    main()
