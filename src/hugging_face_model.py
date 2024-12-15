import requests
import configparser


def generate_response(prompt, api_token, model="mistralai/Mistral-7B-Instruct-v0.3"):
    try:
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {api_token}"}

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 2048,
                "temperature": 0.6,
                "top_p": 0.9,
                "repetition_penalty": 1.2,
                "do_sample": True
            }
        }

        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code != 200:
            return f"Error: {response.status_code}, {response.json()}"

        generated_text = response.json()[0]["generated_text"]
        return generated_text

    except Exception as e:
        return f"An error occurred: {e}"


if __name__ == "__main__":
    print("Hugging Face AI Chat")

    CONFIG = configparser.ConfigParser()
    CONFIG.read('../configs/config.ini')

    token = CONFIG['HUGGING_FACE_API']['hugging_face_token']
    # model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    # model_name = "Qwen/Qwen2.5-72B-Instruct"

    while True:
        question = input("You: ")
        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        answer = generate_response(question, token)
        print(f"AI: {answer}")
