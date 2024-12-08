import unittest
import json
from unittest.mock import patch, MagicMock, Mock
import requests
import sys
import os
import configparser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from src.simple import __is_yes_no_question
from src.main import get_random_quote

CONFIG = configparser.ConfigParser()
CONFIG.read('../configs/config.ini')

mistral_token = CONFIG['BOT.MISTRAL']['token']


class TestIsYesNoQuestion(unittest.TestCase):
    @patch('simple.Mistral')  # Mock the Mistral class
    def test_yes_no_question(self, mock_mistral):
        # Mock the API response for a yes/no question
        mock_response = MagicMock()
        mock_response.json.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": "True"
                    }
                }
            ]
        })

        mock_mistral.return_value.__enter__.return_value.chat.complete.return_value = mock_response

        # Call the function with a yes/no question
        result = __is_yes_no_question("Is it raining?", api_key=mistral_token)
        self.assertTrue(result)

    @patch('simple.Mistral')
    def test_non_yes_no_question(self, mock_mistral):
        # Mock the API response for a non-yes/no question
        mock_response = MagicMock()
        mock_response.json.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": "False"
                    }
                }
            ]
        })

        mock_mistral.return_value.__enter__.return_value.chat.complete.return_value = mock_response

        # Call the function with a non-yes/no question
        result = __is_yes_no_question("What is the weather like?", api_key=mistral_token)
        self.assertFalse(result)


class TestGetRandomQuote(unittest.TestCase):

    @patch("requests.get")
    def test_successful_api_response(self, mock_get):
        """Test that a successful API response returns the expected quote."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"q": "Life is beautiful", "a": "Anonymous"}]
        mock_get.return_value = mock_response

        result = get_random_quote()
        self.assertEqual(result, "“Life is beautiful” – Anonymous")

    @patch("requests.get")
    def test_api_error_status_code(self, mock_get):
        """Test that an API error (non-200 status) triggers the fallback."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with patch("random.choice", return_value="Fallback quote"):
            result = get_random_quote()
            self.assertEqual(result, "Fallback quote")

    @patch("requests.get")
    def test_api_exception(self, mock_get):
        """Test that an exception in the API call triggers the fallback."""
        mock_get.side_effect = requests.exceptions.RequestException("API down")

        with patch("random.choice", return_value="Fallback quote"):
            result = get_random_quote()
            self.assertEqual(result, "Fallback quote")

    @patch("random.choice", return_value="Static fallback quote")
    @patch("requests.get", side_effect=Exception("Timeout"))
    def test_fallback_quote_used(self, mock_get, mock_random_choice):
        """Test that a predefined fallback quote is returned when an error occurs."""
        result = get_random_quote()
        self.assertEqual(result, "Static fallback quote")
