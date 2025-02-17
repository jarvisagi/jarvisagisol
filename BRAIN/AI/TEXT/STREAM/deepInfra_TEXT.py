import json
import requests
from typing import Union, Generator
import re

def generate(conversation_history: list, 
              model: str = 'meta-llama/Meta-Llama-3-70B-Instruct', 
              system_prompt: str = "Be Helpful and Friendly. Keep your response straightforward, short and concise", 
              max_tokens: int = 512, 
              temperature: float = 0.7, 
              stream: bool = True, 
              chunk_size: int = 1) -> Union[Generator[str, None, None], str]:
    """
    Utilizes a variety of large language models (LLMs) to engage in conversational interactions.
    
    Parameters:
        - conversation_history (list): A list of dictionaries representing the conversation history including the system prompt.
        - model (str): The name or identifier of the LLM to be used for conversation. Available models include various options.
        - system_prompt (str): The initial system message to start the conversation.
        - max_tokens (int): Optional. The maximum number of tokens to be generated by the LLM. Defaults to 512.
        - temperature (float): Optional. The temperature of the LLM. Defaults to 0.7.
        - stream (bool): Optional. Whether to stream the response from the LLM. Defaults to False.
        - chunk_size (int): Optional. The size of the chunks to be streamed from the LLM. Defaults to 24.

    Models:
            - "meta-llama/Meta-Llama-3-70B-Instruct"
            - "meta-llama/Meta-Llama-3-8B-Instruct" 
            - "mistralai/Mixtral-8x22B-Instruct-v0.1"
            - "mistralai/Mixtral-8x22B-v0.1"
            - "microsoft/WizardLM-2-8x22B"
            - "microsoft/WizardLM-2-7B"
            - "HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1"
            - "google/gemma-1.1-7b-it"
            - "databricks/dbrx-instruct"
            - "mistralai/Mixtral-8x7B-Instruct-v0.1"
            - "mistralai/Mistral-7B-Instruct-v0.2"
            - "meta-llama/Llama-2-70b-chat-hf"
            - "cognitivecomputations/dolphin-2.6-mixtral-8x7b"

    Returns:
        - Union[str, None]: The response message from the LLM if successful, otherwise None.
    """
    api_url = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    headers = {
    "Accept": "text/event-stream",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Dnt": "1",
    "Host": "api.deepinfra.com",
    "Origin": "https://deepinfra.com",
    "Referer": "https://deepinfra.com/",
    "Sec-Ch-Ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "X-Deepinfra-Source": "web-page",
}
    # Insert the system prompt at the beginning of the conversation history
    conversation_history.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": model,
        "messages": conversation_history,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stop": [],
        "stream": True
    }
    
    if stream:
        yield from _stream_response(api_url, headers, payload, chunk_size)
    else:
        return _get_full_response(api_url, headers, payload)

def _stream_response(api_url, headers, payload, chunk_size):
    """Streams the response from the API and yields sentences."""
    partial_sentence = ""
    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=True)
        for value in response.iter_lines(decode_unicode=True, chunk_size=chunk_size):
            modified_value = re.sub("data:", "", value)
            if modified_value and "[DONE]" not in modified_value:
                json_modified_value = json.loads(modified_value)
                try:
                    if json_modified_value["choices"][0]["delta"]["content"] != None:
                        data_chunk = json_modified_value["choices"][0]["delta"]["content"]
                        partial_sentence += data_chunk
                        print(data_chunk, end="", flush=True)
                        sentences = re.split(r'(?<!\b\w\.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', partial_sentence)
                        for complete_sentence in sentences[:-1]:
                            yield complete_sentence.strip()
                        partial_sentence = sentences[-1] 
                except: 
                    continue
        if partial_sentence:
            yield partial_sentence.strip()
    
    except json.JSONDecodeError: 
        pass
    
    except Exception as e:
        print("Error:", e)
        yield "Response content: " + response.text

def _get_full_response(api_url, headers, payload):
    """Retrieves the full response from the API."""
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if response is not None and hasattr(response, 'text'): 
            return f"Response content: {response.text}" 
        else:
            return "An error occurred while fetching the response."
    except json.JSONDecodeError: pass
        # print("Warning: Invalid JSON response received. Continuing...")
    except KeyError as e:
        print(f"Error: Expected key not found in JSON response: {e}")
        if response is not None and hasattr(response, 'text'): 
            return f"Error parsing response: {response.text}" 
        else:
            return "An error occurred while parsing the response."

if __name__ == "__main__":
    # Predefined system prompt
    # system_prompt = "Be Helpful and Friendly. Keep your response straightforward, short and concise"
    system_prompt = "Be Helpful and Friendly. Keep your response straightforward, long and detailed"
    # system_prompt = "Talk like Shakespeare"

    # Predefined conversational history that includes providing a name and then asking the AI to recall it
    conversation_history = [
        {"role": "user", "content": "My name is Sreejan."},
        {"role": "assistant", "content": "Nice to meet you, Sreejan."},
        {"role": "user", "content": "Write 10 Lines about India"}
    ]

    # Call the generate function with the predefined conversational history
    for statement in generate(conversation_history=conversation_history, system_prompt=system_prompt, stream=True):
        print(f"\n\033[91mAI:\033[0m \033[92m{statement}\033[0m")