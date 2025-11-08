import os
import json
import asyncio

from dotenv import load_dotenv
from langchain.globals import set_debug

from google_agent.agent import GoogleAgent
from google_client.api_service import APIServiceLayer
from langchain_core.messages import HumanMessage
from google_agent.shared.llm_models import LLM_FLASH
from argparse import ArgumentParser

load_dotenv()

scopes = [
    'https://www.googleapis.com/auth/calendar',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/drive'
]

async def run_async(messages=None, llm=LLM_FLASH, print_steps=False):
    token_path = os.getenv("TOKEN_PATH")
    creds_path = os.getenv("CREDS_PATH")
    with open(r'C:\Users\dagms\Projects\Credentials\token-1.json', 'r') as f:
        user_info = json.load(f)

    google_service = APIServiceLayer(user_info, timezone='America/New_York')
    agent = GoogleAgent(google_service, llm, print_steps=print_steps)

    if messages is None:
        messages = []
    while True:
        user_input = input("Human: ")
        if user_input == "quit":
            break
        response = await agent.aexecute(messages + [HumanMessage(user_input)])
        messages.extend(response.messages)

        print("AI:", response.messages[-1].content)

    return messages

def run(messages=None, llm=LLM_FLASH, print_steps=False):
    return asyncio.run(run_async(messages, llm, print_steps))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--print_steps", type=str, default="false")
    args = parser.parse_args()
    print_steps = args.print_steps.lower() == "true"
    run(print_steps=print_steps)
