# api/tasks.py
import time
import threading
from datetime import datetime
from django.core.cache import cache
from api.utils import remove_prefix, save_editor_content

CACHE_TIMEOUT = 600  # Cache timeout in seconds
CHECK_INTERVAL = 60  # Interval to check for stale data in seconds

def background_task():
    while True:
        print(f"Running background task at {datetime.utcnow()}")
        current_time = datetime.utcnow()
        keys = cache._cache.keys()
        print(f"Cache keys: {keys}")
        for key in keys:
            if "editor_content_" in key:
                editor_content = cache.get(remove_prefix(key))
                print('editor_content', editor_content['qid'])
                if editor_content and 'last_update' in editor_content:
                    last_update_time = datetime.strptime(editor_content['last_update'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    time_diff = (current_time - last_update_time).total_seconds()
                    print(f"Time diff for {key}: {time_diff} seconds")
                    if time_diff >= CACHE_TIMEOUT - CHECK_INTERVAL:
                        # Extract user_id and qid from key
                        _, _, user_id, qid = key.split("_", 3)
                        print(f"Persisting content for user_id: {user_id}, qid: {qid}")
                        save_editor_content(user_id, qid, editor_content)
        time.sleep(CHECK_INTERVAL)  # Run the check every minute

def start_background_task():
    background_thread = threading.Thread(target=background_task)
    print('Starting background thread')
    background_thread.daemon = True
    background_thread.start()


