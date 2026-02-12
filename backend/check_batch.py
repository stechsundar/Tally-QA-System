from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

batch_id = "msgbatch_01IJTo8FmC8T9WqekHTtbFQk"  # Your batch ID from the screenshot

# Check status
batch = client.messages.batches.retrieve(batch_id)

print(f"Status: {batch.processing_status}")
print(f"Requests: {batch.request_counts}")
print(f"Created: {batch.created_at}")
print(f"Ended: {batch.ended_at}")