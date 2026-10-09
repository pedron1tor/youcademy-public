import datetime
import openai
import os
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from groq import RateLimitError
from langchain_community.callbacks import get_openai_callback
from langchain_community.document_loaders import PyPDFDirectoryLoader
import textwrap
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
import json
import shutil
import openai
import pandas as pd
import os
from copy import deepcopy
from sklearn.preprocessing import LabelEncoder
from keras_preprocessing.text import Tokenizer
import torch
from django.apps import apps
from .dicts import files, metrics_for_writing, get_query, strategy_for_questions, metrics_for_questions
from google.cloud import pubsub_v1
from pages.models import Metrics, BinarySearchParameters
# load environment variables
os.environ["OPENAI_API_KEY"] = settings.OPENAI_KEY
class CreateReading:
  def __init__(self, request, practice_id, course_id): 
    self.user = request.user
    self.files = files 
    self.topic = request.POST["topic"]
    self.lexile_level = request.user.metrics.last().estimated_lexile_level if request.user.metrics.last() and request.user.metrics.last().estimated_lexile_level is not None else 1000
    self.diagnostic = request.user.diagnostic
    self.writing_topics = self.get_metrics_for_writing(["descriptive", "genre", "sequence"])
    self.text = None
    self.practice_id = practice_id
    self.course_id = course_id
  def find_closest_pair(self):
    target_level = self.lexile_level
    print("target level:", target_level)
    files_sorted = sorted(self.files, key=lambda x: x[1])
    closest_files = []
    if target_level <= files_sorted[0][1]:
      closest_files = [files_sorted[0][0], files_sorted[1][0]]
    elif target_level >= files_sorted[-1][1]:
      closest_files = [files_sorted[-2][0], files_sorted[-1][0]]
    else:
      for i in range(len(files_sorted) - 1):
        if files_sorted[i][1] <= target_level <= files_sorted[i + 1][1]:
          closest_files = [files_sorted[i][0], files_sorted[i + 1][0]]
          break

    return closest_files
  
  def get_metrics_for_writing(self, creation_metrics):
    return '\n'.join(metrics_for_writing[metric] for metric in creation_metrics) if creation_metrics else ""
  def gpt_query(self, ):
    query = get_query(self.writing_topics, self.topic, self.lexile_level)
    closest_files = self.find_closest_pair()
    closest_files = [
        os.path.join(settings.BASE_DIR, "static", "pdfs", "levels", file)
        for file in closest_files
    ] 
    filepath = os.path.join(settings.BASE_DIR, "static", "pdfs", "levels_2",
                            str(self.lexile_level))
    os.makedirs(filepath, exist_ok=True)
    for file_path in closest_files:
      shutil.copy(file_path, filepath)
    loader = PyPDFDirectoryLoader(path=filepath, )
    data = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=500,
                                          chunk_overlap=50,
                                          separator="\n")
    docs = text_splitter.split_documents(data)
    shutil.rmtree(filepath)
    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    messages = [("system", query + "\n\n{context}")]
    tries = 0 
    rle = True
    while True:
      try:
        prompt = ChatPromptTemplate.from_messages(messages)
        if settings.PROD:
          if rle:
            llm = ChatOpenAI(
                model_name="gpt-4o-2024-08-06",
                temperature=0.6).bind(response_format={"type": "json_object"})
            model = "gpt-4o-2024-08-06"
          else:
            llm = ChatGroq(model="llama-3.1-70b-versatile", ).bind(response_format={"type": "json_object"})
            model = "llama-3.1-70b-versatile"
        else:
          if rle: 
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.5).bind(response_format={"type": "json_object"})
            model = "gpt-4o-mini"
          else:
            llm = ChatGroq(model="llama-3.1-70b-versatile", ).bind(response_format={"type": "json_object"})
            model = "llama-3.1-70b-versatile"
        with get_openai_callback() as cb:
          chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
          result = chain.invoke({"context": docs, "input": prompt})
          total_tokens = cb.total_tokens
          prompt_tokens = cb.prompt_tokens
          completion_tokens = cb.completion_tokens
          total_cost = cb.total_cost
        response = json.loads(result)
        print(self.lexile_level)
        if tries < 2:
          if 700 <= self.lexile_level <= 1300:
            lexile = self.check_lexile(response["text"], self.lexile_level)
            if not lexile[0]:
              messages.append(("assistant", response["text"]))
              messages.append(("user", f"This text is not at the correct lexile level. This is what my neural network says about it {lexile[1], lexile[2]}, when it should be {self.lexile_level}, study the documents more carefully and try again please."))
                            
            assert lexile[0], "Lexile level not correct"

        assert "title" in response, "no title"
        assert "text" in response, "no text"
        assert type(response["title"]) == str, "title not a string"
        assert type(response["text"]) == str, "text not a string"
        text = response["text"]
        story_title = response["title"]
        settings.MDB_1.readings.insert_one({"title": story_title, "text": text, "query": self.topic, "course_id":self.course_id , "practice_id": str(self.practice_id), "user_id": self.user.id, "lexile_level": self.lexile_level, 
                                            "word_count": len(text.split()), "graded": False, "time": datetime.datetime.now(), "model": model, "total_tokens": total_tokens, "prompt_tokens": prompt_tokens, 
                                            "completion_tokens": completion_tokens, "total_cost": total_cost})
        return (story_title, text, query, None, None, None)
      except RateLimitError: 
        rle = True
      except Exception as e:
        tries += 1
        print("Failed to parse response for story: ", e) 

  def check_lexile(self, text, lexile_level):
    config = apps.get_app_config("classifier")
    model = config.model
    model.eval()
    dictionary = {"text": [text]}
    processor = TextProcessor()
    data_df = pd.DataFrame(dictionary, columns=["text"])
    data_df["tokenized_text"] = data_df["text"].apply(processor.tokenize)
    processor.train_tf_idf_model(data_df["tokenized_text"])
    mat_texts = processor.prepare_model_input(data_df, mode="tfidf")
    input_text = torch.tensor(mat_texts, dtype=torch.float32)
    with torch.no_grad():
      prediction = model(input_text)
      print(prediction)
      predicted_class = torch.argmax(prediction, dim=1)
      lexile_converter = [700, 800, 900, 1000, 1100, 1200, 1300]
      pred_lexile_level = lexile_converter[predicted_class.item()]
      print("Predicted class:", pred_lexile_level)

    return (abs(pred_lexile_level - lexile_level) <= 100, prediction, pred_lexile_level)

class TextProcessor:
    def __init__(self, num_words=4000):
        self.tokenizer = Tokenizer(num_words=num_words)
        self.label_encoder = LabelEncoder()

    def tokenize(self, text):
        lines = (line for line in text.split("\n"))
        return " ".join(" ".join(tok for tok in sentence.split()) for sentence in lines)

    def token_count(self, text):
        return len(text.split())

    def train_tf_idf_model(self, texts):
        self.tokenizer.fit_on_texts(texts)
        return self.tokenizer

    def prepare_model_input(self, dataframe, mode="tfidf"):
        sample_texts = list(dataframe["tokenized_text"])
        sample_texts = [" ".join(x.split()) for x in sample_texts]
        
        if mode == "tfidf":
            sample_texts = self.tokenizer.texts_to_matrix(sample_texts, mode="tfidf")
        else:
            sample_texts = self.tokenizer.texts_to_matrix(sample_texts)
        
        print("shape of data:", sample_texts.shape)
        return sample_texts

class CreateQuestions:
  def __init__(self, request):
    self.user = request.user
    self.lexile_level = request.user.metrics.last().estimated_lexile_level
    self.diagnostic = request.user.diagnostic
    self.writing_topics = self.get_metrics_for_questions(request.user.metrics.last().creation_metrics)
  def gpt_questions(self, question_topics, question_strategy, story, original_query):
    query = textwrap.dedent(
        f"""You are a teacher and are going to assess your students on text comprehension. For the questions, you should carefully follow the instructions provided below.

  {question_topics}

  The student should be nudged for the following reading strategy:

  {question_strategy} Return a json object with the key 'questions' and a list of 15 questions no more, no less. Each question should be a string.  Additionally, include another nested key called "answers" for each of the questions that has 4 possible answers with one that is correct and another key that is 'correct' with boolean values in the same order as the answers.
                            Add one open question in the end, and for this one do not attach any answers under the 'answers' key, but only for this question.  
                            You can create multiple-choice questions, open questions, and highlighting questions. Highlighting questions are questions where students need to highlight the answer in the text.
  Thes string for "type" key should be all lowercase. “multiple” for multiple choice, “highlight” for a highlighting question, “open” for open-ended questions. If the question is a highlighting question, the exact sentence that the student should highlight should be placed in the “correct” key and the answers key should be left empty. 
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
            "correct": []
        }},]}}
                          Please ensure that you strictly adhere to this format and that the you always fill out the answers when they are multiple choice questions"""
        + story)
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
        
        if settings.PROD:
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
        print("got response to mpc quiz:", response)
        quiz = json.loads(response)

        assert type(quiz["questions"]) == list, "not a list"
        highlight_num = 0
        for q in quiz["questions"]:
          assert "question" in q, "no 'question'"

          if q["type"] == "multiple":
            assert "answers" in q, "no 'option'"
            assert "correct" in q, "no 'answer'"
          if q["type"] == "highlight":
            highlight_num += 1

        assert highlight_num == 1, "no highlighting question, more than 1"
        return quiz
      except Exception as e:
        print("Failed to parse response for quiz: ", e)
  def get_question_topics(self, creation_metrics):
    
    if len(creation_metrics) > 0:
      question_topics = "\n".join(
          [strategy_for_questions[metric] for metric in creation_metrics])
    else:
      question_topics = ""
    return question_topics


  def get_metrics_for_questions(self, creation_metrics):
    
    if len(creation_metrics) > 0:
      question_strategy = "\n".join(
          [metrics_for_questions[metric] for metric in creation_metrics])
    else:
      question_strategy = ""
    print("This code ran")
    return question_strategy

class Publisher: 
  def __init__(self, message, data):
    self.message = message
    self.data = data
  def publish(self):
    try:
      publisher = pubsub_v1.PublisherClient()
      topic_name = 'projects/{project_id}/topics/{topic}'.format(
          project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
          topic=os.getenv('TOPIC_NAME'),  # Set this to something appropriate.
      )
      message_data = self.message.encode('utf-8') if isinstance(self.message, str) else self.message
      attributes = {}
      if isinstance(self.data, dict):
        for key, value in self.data.items():
          attributes[key] = str(value)
      future = publisher.publish(topic_name, message_data, **attributes)
      print(future.result())
    except Exception as e: 
      print(e)
    # TODO add logging if pubsub fails

    
class Subscriber: 
  def __init__(self):
    pass

def cefr_to_lexile(cefr):
  cefr_to_lexile = {
      "A1_1": 178,
      "A1_2": 356,
      "A1_3": 534,
      "A2_1": 620,
      "A2_2": 706,
      "A2_3": 792,
      "B1_1": 888,
      "B1_2": 983,
      "B1_3": 1078,
      "B2_1": 1153,
      "B2_2": 1228,
      "B2_3": 1303,
      "C1_1": 1325,
      "C1_2": 1393,
      "C1_3": 1460,
      "C2_1": 1465,
      "C2_2": 1565,
      "C2_3": 1665,
  }
  return cefr_to_lexile[cefr]

def cefr_to_lexile_diagnostic(cefr):
  cefr_to_lexile = {
    "A1_1": (178, 1),
      "A1_2": (356,2),
      "A1_3": (534, 3),
      "A2_1": (620, 4),
      "A2_2": (706, 5),
      "A2_3": (792,6),
      "B1_1": (888, 7),
      "B1_2": (983, 8 ),
      "B1_3": (1078, 9),
      "B2_1": (1153, 10),
      "B2_2": (1228, 11),
      "B2_3": (1303, 12),
      "C1_1": (1325, 13),
      "C1_2": (1393, 14),
      "C1_3": (1460, 15),
      "C2_1": (1465, 16),
      "C2_2": (1565, 17),
      "C2_3": (1665, 18),
  }
  return cefr_to_lexile[cefr]

def rank_to_lexile(rank): 
  cefr_to_lexile= {
    1: 178,
      2:356,
     3: 534,
      4:620,
     5: 706,
     6 :792,
      7:888,
     8 :983,
      9:1078,
      10:1153,
     11 :1228,
     12 :1303,
     13 :1325,
     14 :1393,
     15: 1460,
      16:1465,
      17:1565,
      18:1665, 
  }
  return cefr_to_lexile[rank]
def create_flashcards(): 
  flashcards = {'cards': [{
        "id": 1,
        "frontHTML": "",
        "backHTML": ""
    }], "title": "New Flashcard Set", "topic": "New Flashcard Set"}
  return flashcards 

def teacher_feedback(practice_id, questions, user_answers,):
    # Create a deep copy of the questions dictionary to avoid modifying the original
    graded_questions = deepcopy(questions)
    
    # Parse user answers
    user_answers = json.loads(user_answers['responses'][0])
    questions = graded_questions['quiz']['questions']
    grades = []
    for question in questions:
        q_num = question['question_num']
        q_type = question['type']
        teacher_feedback = user_answers.get(f'question_{q_num}', {}).get('feedbackinput')
        grade = user_answers.get(f'question_{q_num}', {}).get('grade')
        if q_type == 'highlight':
            settings.MDB_1.questions.update_one(
                {"practice_id": practice_id, "quiz.questions.question_num": q_num},
                {"$push": {
                    "quiz.questions.$.feedback": {
                        "type": "Teacher",
                        "message": teacher_feedback}, }, "$set": { "quiz.questions.$.grade": grade}}, 
                
            )
            grades.append(int(grade))
        elif q_type == 'open':
            settings.MDB_1.questions.update_one(
                {"practice_id": practice_id, "quiz.questions.question_num": q_num},
                {"$push": {
                    "quiz.questions.$.feedback": {
                        "type": "Teacher",
                        "message": teacher_feedback
                    }
                }, 
                "$set": {
            "quiz.questions.$.grade": grade}}
            )
            grades.append(int(grade))
    
    mpc_grade = settings.MDB_1.questions.find_one({"practice_id": practice_id})['mpc_grade']
    print(grades, questions, mpc_grade)
    total_grade = (sum(grades)+mpc_grade*(len(questions)-len(grades)))/len(questions)
    settings.MDB_1.questions.update_one({"practice_id": practice_id}, {"$set": {"teacher_graded": True, "total_score": total_grade}})
    settings.MDB_1.readings.update_one({"practice_id": practice_id}, {"$set": {"teacher_graded": True, "total_score": total_grade}})

class LexileAlgorithm:
  def __init__(self, request, score): 
    self.request = request
    self.user = request.user
    self.score = score
    self.last_metric = self.user.metrics.last()

  def BinarySearch(self): 
    object, created = BinarySearchParameters.objects.get_or_create(user=self.user)
    if created:
      low = 1
      high = 18
      object.low = low
      object.high = high
      past_cefr = self.last_metric.estimated_cefr_rating
      past_level = self.last_metric.estimated_level
      mid = cefr_to_lexile_diagnostic(past_cefr+"_"+past_level)[1]
    else: 
      low = object.low
      high = object.high
      mid = (low + high) // 2
    # TODO add a way to test the hypothesis that teachers have no idea about their students regarding their level...
    while low <= high:
        if self.score >= 80:
          # If student passes this level, try a higher one
          low = mid + 1
          self.update_student_metrics(lexile=rank_to_lexile(mid))
          object.low = low
          break
        else:
          # If student fails this level, try a lower one
          high = mid - 1
          object.high = high
          self.update_student_metrics(lexile=rank_to_lexile(mid))
          break
    object.save()
    if low > high:
      return True
    else: 
      return False
    
  def update_student_metrics(self, lexile=None, cefr_rating=None):
    if lexile: 
      new_metrics = Metrics(student=self.user, estimated_lexile_level=lexile)
      new_metrics.save()
    elif cefr_rating: 
      Metrics(student=self.user, estimated_cefr_rating=cefr_rating)
