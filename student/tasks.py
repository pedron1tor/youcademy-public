from google.cloud import tasks_v2
from google.protobuf import duration_pb2
import json
from django.conf import settings

class TaskHandler:
  def __init__(self, task_handler_url, payload):
    self.url = task_handler_url
    self.payload = payload

  def enqueue_question_generation(self):
    # modularity for future processing...
    return self.create_task(self.payload)
  
  def enqueue_notes_procesing(self): 
    return self.create_task(self.payload)
  
  def highlight_processing(self):
    return self.create_task(self.payload)

  def create_task(self, payload):
    client = tasks_v2.CloudTasksClient()
    project = "your-gcp-project-id"
    queue = "questiongen"
    location = "us-central1"
    parent = client.queue_path(project, location, queue)
    task = {
      'http_request': {
        'http_method': tasks_v2.HttpMethod.POST,
        'url': self.url,
        'oidc_token': {
          'service_account_email': 'cloud-tasks-invoker@your-gcp-project-id.iam.gserviceaccount.com',
          'audience': self.url
        },
        'headers': {'Content-type': 'application/json'},
        'body': json.dumps(payload).encode()
      }
    }
    response = client.create_task(request={"parent": parent, "task": task})
    return response.name