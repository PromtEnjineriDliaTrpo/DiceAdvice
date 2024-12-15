import random
import requests


# Fallback Quotes (in case API fails)
FALLBACK_QUOTES = [
    "“The only limit to our realization of tomorrow is our doubts of today.” – Franklin D. Roosevelt",
    "“In the middle of every difficulty lies opportunity.” – Albert Einstein",
    "“Success is not final, failure is not fatal: It is the courage to continue that counts.” – Winston Churchill",
    "“Happiness is not something ready-made. It comes from your own actions.” – Dalai Lama",
    "“Your time is limited, don’t waste it living someone else’s life.” – Steve Jobs",
    "“Life is what happens when you’re busy making other plans.” – John Lennon"
]


# Function to fetch a random quote from an API
def get_random_quote():
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            quote = f"“{data[0]['q']}” – {data[0]['a']}"
            return quote
        else:
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        print(f"Error fetching quote: {e}")
        # Fallback to a predefined quote
        return random.choice(FALLBACK_QUOTES)