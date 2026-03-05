import requests

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather?"

    def get_weather(self, city):
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

class UserService:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_user(self, user_id):
        url = f"{self.base_url}/{user_id}"
        response = requests.get(url)
        return response.json()

class EmailService:
    def send_email(self, recipient, subject, body):
        payload = {
            'to': recipient,
            'subject': subject,
            'body': body
        }
        response = requests.post("https://api.sendgrid.com/v3/mail", json=payload)
        return response.status_code == 202