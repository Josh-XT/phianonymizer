# PHI Anonymizer

PHI (Protected Health Information) Anonymizer is a tool designed to help you anonymize sensitive information in your text data. It uses advanced natural language processing techniques to identify and redact sensitive information such as names, addresses, and medical terms.

## Disclaimer

This tool is best-effort and could still miss sensitive information, it also depends on which LLM is used on the quality of results. All feedback we receive will go towards improving it. Use at your own risk.

## Usage

### Install

```bash
pip install phianonymizer
```

### Example usage

```python
from phianonymizer import anonymize_text, deanonymize_text

original_text = "Hi! My name is Bobby Smith, I was born on 01/04/1970 in New York City. My phone number is 626-433-7890 and my email is bobby.smith@gmail.com. You probably need my social security number too, it's 213-45-6919. So what have you learned about me?"
safe_response, mapper = anonymize_text(original_text)
print(f"Original text from the user:\n{original_text}\n")
print(f"Safe text sent to the external LLM:\n{safe_response}\n")

# Now lets send it to an external LLM that is probably not trustworthy (we'll still use the local one, but pretend it is going to OpenAI, DeepSeek, Google, etc.)
response = mapper.llm.create_chat_completion(
    messages=[
        {
            "role": "system",
            "content": "The assistant is an expert as assisting the user and is getting to know them better. The assistant is very friendly and helpful.",
        },
        {
            "role": "user",
            "content": f"{safe_response}",
        },
    ],
    temperature=0.4,
    max_tokens=2048,
)

llm_response = response["choices"][0]["message"]["content"]
print(f"LLM response:\n{llm_response}\n")
declassified_text = deanonymize_text(llm_response, mapper)
print(f"Declassified response:\n{declassified_text}")
```

Replace the `response` section with using something like your OpenAI API or other LLM provider to anonymize the text before sending it to the LLM, and then deanonymize the response after receiving it.

### Example output

```bash
Original text from the user:
Hi! My name is Bobby Smith, I was born on 01/04/1970 in New York City. My phone number is 626-433-7890 and my email is bobby.smith@gmail.com. You probably need my social security number too, it's 213-45-6919.

Safe text sent to the external LLM:
Hi! My name is John, I was born on 01/04/1970 in New York City. My phone number is 378-602-8003 and my email is bobby.smith@gmail.com. You probably need my social security number too, it's 123456789.

LLM response:
Hello John! Thank you for sharing your information. It's great that you've provided your contact details. If you have any questions or need assistance with something related to your information, feel free to ask. I'm here to help.

Declassified response:
Hello Bobby Smith! Thank you for sharing your information. It's great that you've provided your contact details. If you have any questions or need assistance with something related to your information, feel free to ask. I'm here to help.
```

## Technical Details

We're using a combination of [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) and a quantized version of the [Qwen 0.5B model](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct).

If you have the CUDA version of llama-cpp-python installed, this will run on GPU. Otherwise, it will run on CPU.

The `Qwen 0.5B` model runs on very little RAM and can be run on CPU very quickly still. Putting a more powerful model in would greatly improve the quality of the anonymization, but would also increase the cost and complexity of running this tool. To change which model is used, change the `model_repo` and `model_filename` parameters in the `anonymize_text` function. Here's an example of how to do that:

```python
from phianonymizer import anonymize_text

anonymized_text, mapper = anonymize_text(
    text="My name is Bobby Smith, I was born on 01/04/1970 in New York City. My phone number is 626-433-7890 and my email is bobby@smith.org. You probably need my social security number too, it's 213-45-6919. What have you learned about me?",
    model_repo="bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    model_filename="*Q4_K_M.gguf",
)
```

## Contributing

We welcome contributions to this project! If you have an idea for a new feature or improvement, please open an issue or submit a pull request.

## License

MIT License, see [LICENSE](LICENSE) for details.
