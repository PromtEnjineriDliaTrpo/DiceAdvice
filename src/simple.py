from mistralai import Mistral
import json

api_key = '3Hc4mDWfCKf0H6H3MJDwxCcHX8HpZA4d'

def is_yes_no_question(question, api_key):
    with Mistral(
        api_key=api_key,
    ) as s:
        res = s.chat.complete(model="mistral-large-latest", messages=[
            {
                "role": "system",
                "content": "You are an assistant that determines if a question can be answered with 'yes' or 'no'. Respond only with 'True' if it's a yes/no question, or 'False' if it's not."
            },
            {
                "role": "user",
                "content": f"Is this a yes/no question: '{question}'? Respond only with True or False."
            },
        ])

        if res is not None:
            print(res.json())
            js = json.loads(res.json())
            result = js['choices'][0]['message']['content'].strip().lower()
            return result == "true"