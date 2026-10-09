from fsrs import *

f = FSRS()
# all new cards are 'due' immediately upon creation
card = Card()
# you can choose one of the four possible ratings
"""
Rating.Again # forget; incorrect response
Rating.Hard # recall; correct response recalled with serious difficulty
Rating.Good # recall; correct response after a hesitation
Rating.Easy # recall; perfect response
"""

rating = Rating.Good

card, review_log = f.review_card(card, rating)
from datetime import datetime, timezone

due = card.due

# how much time between when the card is due and now
time_delta = due - datetime.now(timezone.utc)

print(f"Card due: at {repr(due)}")
print(f"Card due in {time_delta.seconds} seconds")

"""
> Card due: at datetime.datetime(2024, 7, 12, 18, 16, 4, 429428, tzinfo=datetime.timezone.utc)
> Card due in: 599 seconds
"""