import functions_framework
import json
from copy import deepcopy
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import openai
@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    os.environ["OPENAI_API_KEY"] = ""
    request_json = request.get_json(silent=True)
    course_id = request_json.get('course_id')
    answers = request_json.get('answers')
    practice_id = request_json.get('practice_id')
    PROD = request_json.get('PROD')
    user_id = request_json.get('user_id')
    uri = "" if PROD else  ""
    client = MongoClient(uri, server_api=ServerApi('1'))

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    MDB = client.reading
    quiz = MDB.questions.find_one({"practice_id": practice_id})
    story = MDB.readings.find_one({"practice_id": practice_id})['text']
    results = grade_quiz(story, quiz, answers, course_id, user_id)
    MDB.questions.update_one({"practice_id": practice_id}, {"$set": results})
    MDB.readings.update_one({"practice_id": practice_id},  {"$set": { "graded": True}})
    return "Success"

def grade_quiz(story, questions, user_answers, course_id, user_id):
    # Create a deep copy of the questions dictionary to avoid modifying the original
    graded_questions = deepcopy(questions)
    
    # Parse user answers
    user_answers = json.loads(user_answers['responses'][0])
    mpc_count = 0
    mpc_grade = 0
    for question in graded_questions['quiz']['questions']:
        q_num = question['question_num']
        q_type = question['type']
        user_answer = user_answers.get(f'question_{q_num}', {}).get('forminput')
        
        if q_type == 'multiple':
            correct_index = question['correct_index']
            correct_answer = question['answers'][int(correct_index)]
            is_correct = user_answer == correct_answer
            user_answer_index = question['answers'].index(user_answer) if user_answer in question['answers'] else None
            
            # Add grading information directly to the question dictionary
            question['user_answer'] = user_answer
            question['user_answer_index'] = user_answer_index
            question['is_correct'] = is_correct
            mpc_count += 1
            mpc_grade += is_correct
        elif q_type == 'highlight':
            correct_highlight = question['correct_highlight'].strip()
            user_highlights = user_answers.get(f'question_{q_num}', {}).get('highlights', {}).get('yellow', [])
            highlighted_text = ' '.join([highlight['text'] for highlight in user_highlights]).strip()
            correct_chars = set(correct_highlight)
            highlighted_chars = set(highlighted_text)
            correct_chars_highlighted = len(correct_chars.intersection(highlighted_chars))
            total_correct_chars = len(correct_chars)
            grade = (correct_chars_highlighted / total_correct_chars) * 100 if total_correct_chars > 0 else 0           
            question['user_answer'] = highlighted_text
            question['grade'] = round(grade, 2)  
            custom_message = [{"role": "system", "content": f"Given this story. {story}. And this question {question['question']} Grade the user's answer."}, {"role": "user", "content": f"This is my answer: {highlighted_text}"}]
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=custom_message,
            )
            question['feedback'] = [{"type": "AI","message" : response.choices[0].message.content}]
            question['yellow_highlights'] = user_highlights 
        
        elif q_type == 'open':
            # Add user answer directly to the question dictionary
            question['user_answer'] = user_answer
            custom_message = [{"role": "system", "content": f"Given this story. {story}. And this question {question['question']} Grade the user's answer. Return positive feedback. Return only text."}, {"role": "user", "content": f"This is my answer: {user_answer}"}]
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=custom_message,
            )
            question['feedback'] = [{"type": "AI","message" : response.choices[0].message.content}]
            question['grade'] = 100
    graded_questions['graded'] = True
    graded_questions['course_id'] = course_id
    graded_questions['user_id'] = user_id
    graded_questions['mpc_grade'] = (mpc_grade / mpc_count) * 100 if mpc_count > 0 else 0
    return graded_questions

