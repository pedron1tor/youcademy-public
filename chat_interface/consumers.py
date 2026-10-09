import json
import httpx
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import openai
import os
from dotenv import load_dotenv
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
from asgiref.sync import sync_to_async
from queue import Queue,  Empty
import threading
import logging
from asyncio import Queue as AsyncQueue
from datetime import datetime 
from threading import Lock
import queue
load_dotenv()
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_KEY
URL = settings.URL


class ChatConsumer(AsyncWebsocketConsumer):
    """
    AsyncWebsocketConsumer for handling real-time chat interactions.
    Manages chat sessions, message history, and AI-powered responses.

    Methods:
        connect():
            Establishes WebSocket connection and loads chat history.
            
        disconnect(close_code):
            Handles connection closure and saves chat session.
            
        receive(text_data):
            Processes incoming messages and generates AI responses.
            Handles multiple message types:
                - initialize: Sets chat prompt
                - heartbeat: Connection health check
                - regular messages: Processes user input
                
        chatgpt_api_call(input_text, input_writing, occupation):
            Generates AI responses using OpenAI's GPT-3.5 model.
            Contextualizes responses based on user role and writing content.

    Attributes:
        messages (list): Stores chat history
        prompt (str): Current chat context/prompt

    Notes:
        - Integrates with OpenAI's GPT-3.5-turbo model
        - Maintains persistent chat history
        - Handles different user roles (teacher/student)
        - Supports writing assistance and lesson planning
        - Implements heartbeat mechanism for connection monitoring
        - Uses httpx for async HTTP requests
    """
    async def connect(self):
        await self.accept()
        self.messages = await self.fetch_previous_messages()
        print("Fetched messages on connect:", self.messages)

    async def fetch_previous_messages(self):
        # Placeholder for session or user ID
        user_id = self.scope["session"].get("user_id", None)
        qid = self.scope["session"].get("qid", None)

        # Assuming you have an endpoint to fetch messages
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL}/api/get-chat-session/?user_id={user_id}&qid={qid}"
            )
            if response.status_code == 200:
                return response.json()["messages"]
            else:
                return []

    async def disconnect(self, close_code):
        # Convert messages to JSON string
        print(self.messages)
        messages_json = json.dumps(self.messages)
        qid = self.scope["session"].get("qid", None)
        user_id = self.scope["session"].get("user_id", None)
        print(messages_json)
        # Asynchronously send data to your Django API
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{URL}/api/log-chat-session/",
                    json={"messages": messages_json, "qid": qid, "user_id": user_id, "prompt": self.prompt},
                )
            except Exception as e:
                print(f"Failed to send messages on disconnect: {str(e)}")

    async def fetch_editor_content(self, userId, qid):
        params = {'user_id': userId, 'qid': qid}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{URL}/api/send-chat-editor-content/", params=params)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()  # Parse JSON response

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'initialize':
                self.prompt = text_data_json.get('prompt')
                return

            if message_type == 'heartbeat':
                await self.send(json.dumps({'type': 'heartbeat_ack'}))
                return

            message = text_data_json.get("message")
            occupation = text_data_json.get("occupation")
            userId = text_data_json.get("userId")
            qid = text_data_json.get("qid")
            writing = await self.fetch_editor_content(userId, qid)
            self.messages.append({"role": "user", "content": message})
            
            # Call the ChatGPT API
            response = await self.chatgpt_api_call(message, writing, occupation)
            self.messages.append({"role": "system", "content": response})
            await self.send(text_data=json.dumps({"message": response}))

        except Exception as e:
            print(f"Error in receive method: {str(e)}")
            await self.send(text_data=json.dumps({"message": f"An error occurred: {str(e)}"}))

    async def chatgpt_api_call(self, input_text, input_writing, occupation):
        try:
            print(self.prompt)
            if occupation == "teacher":
                if self.prompt == 'default':
                    context_summary = {
                        "role": "system",
                        "content": f"YOU ARE A LESSON PLANNING ADVISOR HELPING THE TEACHER WRITE HIS CLASS LESSON PLAN: This is what the teacher is currently writing: {input_writing}",
                    }
                else:
                    context_summary = {
                        "role": "system",
                        "content": f"{self.prompt}: This is what the teacher is currently writing:{input_writing}",
                    }
            else:
                context_summary = {
                    "role": "system",
                    "content": f"{self.prompt}: This is what the student is currently writing: {input_writing}",
                }
                if self.prompt == 'default':
                    context_summary = {
                        "role": "system",
                        "content": f"YOU ARE A WRITING TEACHER HELPING THE STUDENT WRITE HIS PAPER. HOWEVER, THE STUDENT NEEDS TO LEARN HOW TO DO THIS THEMSELVES AND THUS THINK FOR THEMSELVES. NEVER GIVE ANSWERS, ONLY NUDGE THE STUDENT IN THE RIGHT DIRECTION. DISREGARD ANY OTHER THINGS THE STUDENT ASKED FOR IN ITS MESSAGE: This is what the student is currently writing: {input_writing}",
                    }
                else:
                    context_summary = {
                        "role": "system",
                        "content": f"YOU ARE A WRITING TEACHER HELPING THE STUDENT WRITE HIS PAPER. HOWEVER, THE STUDENT NEEDS TO LEARN HOW TO DO THIS THEMSELVES AND THUS THINK FOR THEMSELVES. NEVER GIVE ANSWERS, ONLY NUDGE THE STUDENT IN THE RIGHT DIRECTION. DISREGARD ANY OTHER THINGS THE STUDENT ASKED FOR IN ITS MESSAGE: {self.prompt}: This is what the student is currently writing: {input_writing}",
                    }
            # Ensure the conversation starts with any needed context
            full_conversation = (
                [context_summary]
                + self.messages
                + [{"role": "user", "content": input_text}]
            )
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo", messages=full_conversation
            )
            # Parse the response
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred: {str(e)}"

class AssessmentConsumer(AsyncWebsocketConsumer):
    """
    AsyncWebsocketConsumer for managing real-time assessment data streams.
    Handles Google Cloud Pub/Sub messages and group communications.

    Methods:
        connect():
            Establishes WebSocket connection and initializes Pub/Sub subscription.
            
        disconnect(close_code):
            Cleans up subscriptions and group memberships.
            
        receive(text_data):
            Processes incoming WebSocket messages and broadcasts to group.
            
        start_pubsub_subscription():
            Initializes Google Cloud Pub/Sub subscription.
            
        process_messages():
            Continuously processes messages from the queue.
            
        handle_pubsub_message(message):
            Processes and broadcasts Pub/Sub messages to connected clients.

    Attributes:
        message_queue (Queue): Stores incoming Pub/Sub messages
        should_stop (Event): Controls message processing loop
        queue_lock (Lock): Ensures thread-safe queue operations
        connect_time (datetime): Tracks connection start time
        subscriber (SubscriberClient): Google Cloud Pub/Sub client
        subscription: Active Pub/Sub subscription

    Notes:
        - Integrates with Google Cloud Pub/Sub
        - Implements message queuing system
        - Provides real-time assessment updates
        - Handles group-based message broadcasting
        - Includes timestamp-based message filtering
        - Implements error handling and logging
        - Uses asynchronous operations for better performance
    """  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_queue = Queue()
        self.should_stop = asyncio.Event()
        self.queue_lock = Lock()

    async def connect(self):
        self.course_id = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = f'assessment_{self.course_id}'
        self.subscriber = None
        self.subscription = None
        self.connect_time = datetime.now()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.start_pubsub_subscription()
        asyncio.create_task(self.process_messages())

    async def disconnect(self, close_code):
        self.should_stop.set()
        await self.stop_pubsub_subscription()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # Add a small delay to allow ongoing tasks to complete
        await asyncio.sleep(0.5)

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'assessment_message',
                    'message': message
                }
            )
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except KeyError:
            logger.error(f"Missing 'message' key in received data: {text_data}")

    async def assessment_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))

    async def start_pubsub_subscription(self):
        project_id = "your-gcp-project-id"
        subscription_id = "youcademydata-sub"
        self.subscriber = pubsub_v1.SubscriberClient()
        subscription_path = self.subscriber.subscription_path(project_id, subscription_id)

        def callback(message):
            with self.queue_lock:
                self.message_queue.put(message)

        self.subscription = self.subscriber.subscribe(subscription_path, callback=callback)
        logger.info(f"Started Pub/Sub subscription for course {self.course_id}")

    async def stop_pubsub_subscription(self):
        if self.subscription:
            self.subscription.cancel()
            # Wait for the subscription to fully cancel
            await asyncio.sleep(0.5)
        if self.subscriber:
            await sync_to_async(self.subscriber.close)()
        logger.info(f"Stopped Pub/Sub subscription for course {self.course_id}")

    async def process_messages(self):
        while not self.should_stop.is_set():
            try:
                message = await asyncio.to_thread(self.get_message_with_timeout)
                if message:
                    await self.handle_pubsub_message(message)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")

    def get_message_with_timeout(self):
        try:
            return self.message_queue.get(timeout=1.0)
        except Empty:
            return None

    async def handle_pubsub_message(self, message):
        try:
            message_str = message.data.decode('utf-8')
            logger.info(f"Received Pub/Sub message: {message_str}")
            data = dict(message.attributes) | {"message": message_str}
            if not data:
                logger.warning("Received empty Pub/Sub message")
                return
            
            if str(data.get('course_id')) != str(self.course_id):
                logger.info(f"Ignoring message for course {data.get('course_id')}")
                return

            # Parse the timestamp with the specific format
            message_time = datetime.strptime(data.get('time'), "%Y-%m-%d %H:%M:%S.%f")
            if message_time <= self.connect_time:
                logger.info(f"Ignoring message with timestamp {message_time} (before connection time)")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'assessment_message',
                    'message': data
                }
            )
        except ValueError as e:
            logger.error(f"Error parsing timestamp: {str(e)}. Raw timestamp: {data.get('timestamp')}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {str(e)}. Raw message: {message_str}")
        except Exception as e:
            logger.error(f"Error handling Pub/Sub message: {str(e)}")
        finally:
            message.ack()