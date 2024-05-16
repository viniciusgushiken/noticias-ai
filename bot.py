import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pathlib import Path

# OpenAI instance
client = OpenAI(api_key="your-api-key")

# The URL from which we are fetching the main page data
base_url = "https://braziljournal.com/negocios/"

# Telegram Bot API credentials
# Create a Telegram Bot: Use the BotFather in Telegram to create a new bot. After you create the bot, you will receive a token.
telegram_token = "your-bot-token"

# Get Your Telegram Group Chat ID:
# Add your bot to the group.
# Send a message to the group.
# Use the https://api.telegram.org/bot<YourBotToken>/getUpdates endpoint in your browser to get the chat ID of your group.
telegram_chat_id = "your-chat-id"


# Function to send a message to Telegram group
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Check that the request was successful

def send_telegram_audio(audio_file_path):
    url = f"https://api.telegram.org/bot{telegram_token}/sendAudio"
    files = {'audio': open(audio_file_path, 'rb')}
    data = {'chat_id': telegram_chat_id}
    response = requests.post(url, files=files, data=data)
    response.raise_for_status()  

# Function to generate speech from text
def text_to_speech(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    speech_file_path = Path(__file__).parent / "audio_resumo.mp3"
    response.stream_to_file(speech_file_path)
    return speech_file_path


# Function to fetch HTML content from a URL
def fetch_html(url):
    response = requests.get(url)
    response.raise_for_status()  
    return response.text

# Function to parse links from the main page
def parse_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return [a['href'] for a in soup.select('.boxarticle-infos-title a')]

# Function to scrape the content and title from each linked page
def scrape_content_and_title(link):
    html_content = fetch_html(link)
    soup = BeautifulSoup(html_content, 'html.parser')
    content_div = soup.find('div', class_='post-content-text')
    content = content_div.get_text(strip=True) if content_div else "No content found"
    title_tag = soup.find('h1', class_='post-header-title')
    title = title_tag.get_text(strip=True) if title_tag else "No title found"
    return title, content

# Function to summarize content using OpenAI
def summarize_content(content):
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in summarizing journalistic texts. Your task is to extract the most relevant information from the article and summarize it in bullet points."},
            {"role": "user", "content": f"Summarize this report in bullet points:\n\n{content}"},
        ]
    )
    return response.choices[0].message.content

# Fetch the main page
main_page_html = fetch_html(base_url)

# Parse all links from the main page
links = parse_links(main_page_html)

# Iterate over each link to fetch, extract title, and summarize the content
for link in links:
    title, content = scrape_content_and_title(link)
    summary = summarize_content(content)
    message = f"<b>{title}</b> \n\n<b>Resumo:</b>\n{summary}\n<b>Link:</b> {link}"
    send_telegram_message(message)
    
    # Generate and send the audio file
    audio_file_path = text_to_speech(summary)
    send_telegram_audio(audio_file_path)
    print("Reportagem enviada!")

print("Reportagens enviadas com sucesso!")