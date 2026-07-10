# OpenAI Python SDK - AsyncOpenAI and Chat Completions

## Installation
pip install openai

## AsyncOpenAI Client Creation

```python
import os
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
```

## Chat Completions API

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def main():
    completion = await client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {"role": "developer", "content": "Talk like a pirate."},
            {"role": "user", "content": "How do I check if a Python object is an instance of a class?"},
        ],
    )
    print(completion.choices[0].message.content)

asyncio.run(main())
```

## Error Handling

All errors inherit from openai.APIError:
- openai.APIConnectionError - Network/connection issues
- openai.APIStatusError - HTTP error responses (has status_code and response)
- openai.RateLimitError - 429 status code
- openai.APITimeoutError - Request timeout

Error codes:
- 400: BadRequestError
- 401: AuthenticationError
- 403: PermissionDeniedError
- 404: NotFoundError
- 422: UnprocessableEntityError
- 429: RateLimitError
- >=500: InternalServerError

```python
import openai
from openai import OpenAI

client = OpenAI()

try:
    client.fine_tuning.jobs.create(model="gpt-4o", training_file="file-abc123")
except openai.APIConnectionError as e:
    print("The server could not be reached")
    print(e.__cause__)
except openai.RateLimitError as e:
    print("A 429 status code was received; we should back off a bit.")
except openai.APIStatusError as e:
    print("Another non-200-range status code was received")
    print(e.status_code)
    print(e.response)
```

## Retries

Certain errors are automatically retried 2 times by default with exponential backoff:
- Connection errors
- 408 Request Timeout
- 409 Conflict
- 429 Rate Limit
- >=500 Internal errors

```python
from openai import OpenAI

client = OpenAI(max_retries=0)  # default is 2

# Per-request override
client.with_options(max_retries=5).chat.completions.create(...)
```

## Timeouts

Default timeout is 10 minutes. Configure with:

```python
from openai import OpenAI
import httpx

client = OpenAI(timeout=20.0)  # 20 seconds

# Granular control
client = OpenAI(timeout=httpx.Timeout(60.0, read=5.0, write=10.0, connect=2.0))
```

## Request IDs

All responses provide a _request_id property:

```python
response = await client.responses.create(model="gpt-5.5", input="Say test")
print(response._request_id)  # req_123
```

For failed requests, catch APIStatusError to access request_id.
