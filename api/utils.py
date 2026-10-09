import re
from datetime import datetime
from django.conf import settings
from django.utils import timezone

def remove_prefix(key):
    pattern = re.compile(r":\d+:")
    return pattern.sub("", key)

def save_editor_content(user_id, qid, editor_content):
    print(f"Save editor content for user_id: {user_id}, qid: {qid}")
    words = editor_content["blocks"][0]["content"][0]["text"].split(" ")
    first_five_words = words[:5]
    
    if settings.MDB.writing.find_one({"_id": qid}):
        print(f"Updating existing document for qid: {qid}")
        settings.MDB.writing.update_one(
            {"_id": qid},
            {
                "$set": {
                    "content": editor_content,
                    "updated_at": timezone.now().isoformat(),
                }
            },
        )
    else:
        print(f"Inserting new document for qid: {qid}")
        settings.MDB.writing.insert_one(
            {
                "_id": qid,
                "user_id": int(user_id),
                "content": editor_content,
                "title": " ".join(first_five_words),
                "created_at": timezone.now().isoformat(),
                "updated_at": timezone.now().isoformat(),
                "type": "writing",
                "deadline": "undefined",
            }
        )

