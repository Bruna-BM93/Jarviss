import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_response(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return str(e)
