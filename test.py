import os

from dotenv import load_dotenv
from langchain.globals import set_debug

from google_agent.agent import GoogleAgent
from google_client.user_client import UserClient
from langchain_core.messages import HumanMessage
from google_agent.shared.llm_models import LLM_FLASH
from argparse import ArgumentParser

load_dotenv()

set_debug(True)

def run(messages=None, llm=LLM_FLASH, print_steps=False):
    token_path = os.getenv("TOKEN_PATH")
    creds_path = os.getenv("CREDS_PATH")
    google_service = UserClient.from_file(token_path, creds_path)
    agent = GoogleAgent(google_service, llm, print_steps=print_steps)

    if messages is None:
        messages = []
    while True:
        user_input = input("Human: ")
        if user_input == "quit":
            break
        response = agent.execute(messages + [HumanMessage(user_input)])
        messages.extend(response.messages)

        print("AI:", response.messages[-1].content)

    return messages

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--print_steps", type=bool, default=False)
    args = parser.parse_args()
    print_steps = args.print_steps
    run(print_steps=print_steps)
