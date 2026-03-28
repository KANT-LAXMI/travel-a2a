import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# ✅ LOAD .env FIRST
load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

if not API_KEY or not ENDPOINT or not DEPLOYMENT:
    raise RuntimeError(
        "Azure OpenAI environment variables not set. "
        "Check .env file."
    )

client = AzureOpenAI(
    api_key=API_KEY,
    api_version=VERSION,
    azure_endpoint=ENDPOINT
)

def ask_llm(system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    )
    return response.choices[0].message.content.strip()


