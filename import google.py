from google import genai

# Create the client
client = genai.Client(api_key=AIzaSyDTeeh0iZGKlhb11mETvWQ0jCh58FQC2q8)

# Make the request
response = client.models.generate_content(
    model="gemini-2.0-flash", 
    contents="Is the new API working?"
)

print(response.text)