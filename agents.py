from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from deepgram.client import DeepgramClient, SpeakOptions
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["DEEPGRAM_API_KEY"] = os.environ.get("DEEPGRAM_API_KEY")

def get_response(query):
    llm = ChatGroq(temperature = 0.4, model_name="llama3-8b-8192")

    prompt = PromptTemplate(
        input_variables=["user_query"],
        template="""
        Answer this user query : {user_query}
        """
    )

    chain = prompt | llm
    response = chain.invoke({"user_query" : query})  

    return response.content

def text_to_speech(transcript):
    try:
        deepgram = DeepgramClient()
        speak_options = {"text": transcript}

        options = SpeakOptions(
            model="aura-stella-en",
            encoding="linear16",
            container="wav"
        )

        response = deepgram.speak.v("1").stream(speak_options, options)

        # RETURNS AUDIO BYTES
        return response.stream.getvalue()

    except Exception as e:
        print(f"Exception: {e}")
