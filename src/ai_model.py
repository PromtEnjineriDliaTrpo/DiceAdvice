from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def generate_response(question, model_name="google/flan-t5-large", max_length=1000, temperature=0.9, top_p=0.9):
    try:
        print(f"Loading model: {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        inputs = tokenizer(question, return_tensors="pt")

        outputs = model.generate(
            inputs.input_ids,
            max_length=max_length,
            temperature=temperature,  # Adjust creativity
            top_p=top_p,  # Nucleus sampling for variability
            num_return_sequences=1,
            do_sample=True  # Sampling for diverse outputs
        )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    except Exception as e:
        return f"An error occurred: {e}"


if __name__ == "__main__":
    print("Welcome to the DiceAdvice chatbot! Feel free to ask questions!")
    while True:
        question = input("You: ")
        if question.lower() in ["exit", "quit", "stop"]:
            print("Goodbye!")
            break

        answer = generate_response(question)
        print(f"AI: {answer}")
