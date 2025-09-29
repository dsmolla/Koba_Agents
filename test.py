from agents.gmail.agent import GmailAgent
from google_client.user_client import UserClient
from langchain_core.messages import HumanMessage
from shared.llm_models import MODELS
from langchain_google_genai import ChatGoogleGenerativeAI


token_path = r"C:\Users\dagms\Projects\Credentials\token-1.json"
creds_path = r"C:\Users\dagms\Projects\Credentials\credentials.json"

user = UserClient.from_file(token_path, creds_path)
llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash_lite'])
agent = GmailAgent(user.gmail, llm, print_steps=False)

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
