import functions_framework
import textwrap
import json
import openai
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import io

@functions_framework.http
def hello_http(request):
    os.environ["OPENAI_API_KEY"] = ""
    request_json = request.get_json(silent=True)
    request_args = request.args
    question_topics = request_json.get('question_topics')
    question_strategy = request_json.get('question_strategy')
    story = request_json.get('story')
    original_query = request_json.get('original_query')
    practice_id = request_json.get('practice_id')
    PROD = request_json.get('PROD')
    uri = "" if PROD else ""
    client = MongoClient(uri, server_api=ServerApi('1'))

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    MDB = client.reading
    query = textwrap.dedent(
      f"""You are a teacher and are going to assess your students on text comprehension. For the questions, you should carefully follow the instructions provided below.

{question_topics}

The student should be nudged for the following reading strategy:

{question_strategy} Return a json object with the key 'questions' and a list of 15 questions no more, no less. Each question should be a string.  Additionally, include another nested key called "answers" for each of the questions that has 4 possible answers with one that is correct and another key that is 'correct_index' with the precise zero-index of the answer that is correct.
                          Add one open question in the end, and for this one do not attach any answers under the 'answers' key, but only for this question.  
                          You can create multiple-choice questions, open questions, and highlighting questions. Highlighting questions are questions where students need to highlight the answer in the text.
 Thes string for "type" key should be all lowercase. “multiple” for multiple choice, “highlight” for a highlighting question, “open” for open-ended questions. If the question is a highlighting question, the exact sentence that the student should highlight should be placed in the “correct_highlight” key and the answers key and correct_index should be left empty. 
 Make at least ten multiple choice questions. Also for each question add a key called "question_num" with the number of the question. Please only have ONE highlighting question
  ONLY OUTPUT THE QUESTIONS! NOTHING ELSE. DO NOT return the letter of the questions (a,b,c,d), just return the possible answers for multiple choice
  Please return a JSON file with the questions.
   {{
  "questions": [
      {{
          "question_num": int,
          "question": "",
          “type”: “”,
          "answers": [],
          "correct_index": [], 
          "correct_highlight": "",
      }},]}}
                         Please ensure that you strictly adhere to this format and that the you always fill out the answers when they are multiple choice questions"""
      + story)
    quiz = get_chat_questions(original_query, query, story, PROD)
    MDB.questions.insert_one(
        {
            "practice_id": practice_id,
            "quiz": quiz
        }
    )
    return quiz
def get_chat_questions(original_query, query, story, PROD): 
    while True:
        try:
            custom_message = [
                {
                    "role": "user",
                    "content": original_query
                },
                {
                    "role": "assistant",
                    "content": story
                },
                {
                    "role": "user",
                    "content": query
                },
            ]
            
            if PROD:
                print('using gpt-4')
                response = openai.chat.completions.create(
                    model="ft:gpt-3.5-turbo-0125:youcademy:questions:9VbNoDqo",
                    response_format={"type": "json_object"},
                    messages=custom_message,
                )
            else:
                print('using gpt-3.5')
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=custom_message,
                )

            response = response.choices[0].message.content
            quiz = json.loads(response)

            assert type(quiz["questions"]) == list, "not a list"
            highlight_num = 0
            for q in quiz["questions"]:
                assert "question" in q, "no 'question'"
                if q["type"] == "multiple":
                    assert "answers" in q, "no 'option'"
                    assert "correct_index" in q, "no 'answer'"
                if q["type"] == "highlight":
                    highlight_num += 1
            assert highlight_num == 1, "no highlighting question, more than 1"
            return quiz
        except Exception as e:
            print("Failed to parse response for quiz: ", e)