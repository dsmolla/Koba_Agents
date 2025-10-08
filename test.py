import os

from dotenv import load_dotenv

from google_agent.agent import GoogleAgent
from google_client.user_client import UserClient
from langchain_core.messages import HumanMessage
from google_agent.shared.llm_models import MODELS
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

token_path = os.getenv("TOKEN_PATH")
creds_path = os.getenv("CREDS_PATH")

google_service = UserClient.from_file(token_path, creds_path)
llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
agent = GoogleAgent(google_service, llm, print_steps=True)

def run(messages=None):
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
    run()
