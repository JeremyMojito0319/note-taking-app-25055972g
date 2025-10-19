import warnings
# 忽略 trio 关于已存在自定义 sys.excepthook 的 RuntimeWarning，避免在控制台看到重复警告
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=r"You seem to already have a custom sys\.excepthook handler installed.*"
)
# import libraries
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() # Loads environment variables from .env
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"
# A function to call an LLM model and return the response
def call_llm_model(model, messages, temperature=1.0, top_p=1.0): 
    client = OpenAI(base_url=endpoint,api_key=token)
    response = client.chat.completions.create(
        messages=messages,
        temperature=temperature, top_p=top_p, model=model)
    return response.choices[0].message.content
# A function to translate to target language using the LLM model
def translate_to_language(text, target_language):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that translates text."},
        {"role": "user", "content": f"Translate the following text to {target_language}:\n\n{text}"}
    ]
    return call_llm_model(model, messages)



system_prompt = '''
Extract the user's notes into the following structured fields:
1. Title: A concise title of the notes less than 5 words
2. Notes: The notes based on user input written in full sentences.
3. Tags (A list): At most 3 Keywords or tags that categorize the content of the notes.
Output in JSON format without ```json. Output title and notes in the language: {lang}.
Example:
Input: "Badminton tmr 5pm @polyu".
Output:
{{
  "Title": "Badminton at PolyU", 
  "Notes": "Remember to play badminton at 5pm tomorrow at PolyU.",
  "Tags": ["badminton", "sports"]
}}
'''
# A function to extract structured notes using the LLM model
def extract_structured_notes(text, lang="english"):
    prompt = system_prompt.format(lang=lang)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]
    response = call_llm_model(model, messages)
    return response

#main function for testing
if __name__ == '__main__':
    sample_text = "Badminton tmr 5pm at Polyu"
    print(extract_structured_notes(sample_text, lang="Chinese"))
