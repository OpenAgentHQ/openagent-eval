# tiktoken - Token Counting

## Installation
pip install tiktoken

## Basic Usage

```python
import tiktoken

# Get encoding for a specific model
enc = tiktoken.encoding_for_model("gpt-4o")

# Or get encoding by name
enc = tiktoken.get_encoding("o200k_base")

# Encode text to tokens
tokens = enc.encode("hello world")
print(tokens)  # [15339, 1917]

# Decode tokens back to text
text = enc.decode(tokens)
assert text == "hello world"
```

## Available Encodings

| Encoding Name | Model |
|---------------|-------|
| o200k_base | GPT-4o, GPT-5, GPT-5.5 |
| cl100k_base | GPT-4, GPT-3.5-Turbo |
| p50k_base | Codex models |
| r50k_base | GPT-3 models |
| gpt2 | GPT-2 |

## Token Counting in Messages

```python
import tiktoken

def count_message_tokens(messages, model="gpt-4o"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")
    
    tokens_per_message = 3
    tokens_per_name = 1
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # assistant reply priming
    return num_tokens
```

## Fast Approximate Count

```python
def approximate_token_count(text):
    return len(text) // 4
```

## Performance

tiktoken is 3-6x faster than comparable open source tokenizers:
- Uses BPE (Byte Pair Encoding)
- Reversible and lossless
- Works on arbitrary text
- Compresses text (~4 bytes per token on average)
