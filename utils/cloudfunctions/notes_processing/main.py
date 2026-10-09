import functions_framework
import textwrap
import json
import openai
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import uuid
from datetime import datetime

@functions_framework.http
def hello_http(request):
    os.environ["OPENAI_API_KEY"] = ""
    request_json = request.get_json(silent=True)
    request_args = request.args
    highlighted_text = request_json.get('highlighted_text')
    user_id = request_json.get('user_id')
    unknown_words = request_json.get('unknown_words')
    PROD = request_json.get('PROD')
    uri = "" if PROD else ""
    client = MongoClient(uri, server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    MDB = client.youcademywriting
    print(unknown_words)
    cards = get_flashcard_set(unknown_words)
    new_flashcard = str(uuid.uuid4())
    MDB.flashcards.insert_one(
                {
                    "qid": new_flashcard,
                    "user_id": user_id,
                    "cards": cards["cards"],
                    "title": cards["title"],
                    "topic": cards["topic"],
                    "created_at": datetime.now().isoformat(),
                    "last_viewed": datetime.now().isoformat(),
                }
            )
    print("the cards were uploaded to the mongoDB database")

    return cards

def get_flashcard_set(list_of_words): 
    flashcard_list = {"title": "text", "topic": "text", "cards": [{
        "id": 1,
        "frontHTML": "What is the capital of Alaska?",
        "backHTML": "Juneau"
    }, 
    {
        "id": 2,
        "frontHTML": "What is the capital of California?",
        "backHTML": "Sacramento"
    },
    {
        "id": 3,
        "frontHTML": "What is the capital of New York?",
        "backHTML": "Albany"
    },
    {
        "id": 4,
        "frontHTML": "What is the capital of Florida?",
        "backHTML": "Tallahassee"
    },
    {
        "id": 5,
        "frontHTML": "What is the capital of Texas?",
        "backHTML": "Austin"
    },
    {
        "id": 6,
        "frontHTML": "What is the capital of New Mexico",
        "backHTML": "Santa Fe"
    },
    {
        "id": 7,
        "frontHTML": "What is the capital of Arizona?",
        "backHTML": "Phoenix"
    }]}
    query = textwrap.dedent(
        f"""Please create flashcards for the following words: {list_of_words}. The flashcards should be in a JSON and in the following format DO NOT include any html tags with the cards: 
        {{
    "cards": [
        {{
            "id": int,
            "frontHTML": This is important text,
            "backHTML": "This is the back of the card"
        }},] "title": "text", "topic": "text"}}
        Example with text: 
        \n{json.dumps(flashcard_list, indent=4)}
        """)
    custom_message = [
            {
                "role": "system",
                "content": "You are in charge of teaching students that are learning english as their second language, such that you are in charge of listening to the and returning a JSON file with flashcards. Create one card for each word"
            },
            {
                "role": "assistant",
                "content": query
            },
        ]
    MAX_ATTEMPTS = 5

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=custom_message,
            )
            response = response.choices[0].message.content
            flashcards = json.loads(response)  # type: ignore
            assert type(flashcards["cards"]) == list, "not a list"
            for q in flashcards["cards"]:
                assert "id" in q, "no 'id'"
                assert "frontHTML" in q, "no 'frontHTML'"
                assert "backHTML" in q, "no 'backHTML'"
            return flashcards
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == MAX_ATTEMPTS - 1:
                print("Max attempts reached. Exiting.")
                return {'cards': [{"id": 1, "frontHTML": "","backHTML": ""    }], "title": "New Flashcard Set", "topic": "New Flashcard Set"}