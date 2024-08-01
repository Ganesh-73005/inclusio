import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request,send_file
from google.cloud import translate_v2 as translate
import os
import moviepy.editor as mp
import speech_recognition as sr
import whisper
import subprocess


from gtts import gTTS
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-file.json"

app = Flask(__name__)
locality = ""

translate_client = translate.Client()

def translate_text(text, target_language):
    if not text:
        return ''
    translation = translate_client.translate(text, target_language=target_language)
    return translation['translatedText']

def fetch_latest_news(locality, lang):
    url = f'https://www.vikatan.com/news/{locality}'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return []
    except Exception as err:
        print(f'Other error occurred: {err}')
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    news_section = soup.find_all('div', class_='styles-m__story-card__1N7gZ')
    
    latest_news = []
    base_url = 'https://www.vikatan.com'
    for news in news_section:
        title_tag = news.find('h3')
        link_tag = news.find('a')
        img_tag = news.find('img')
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            link = link_tag['href']
            img_src = img_tag['src']
            if not link.startswith('http'):
                link = base_url + link
            title = translate_text(title, lang)
            read_more="Read More"
            read_more = translate_text(read_more,lang)
            NEWS = "LOCAL NEWS"
            NEWS = translate_text(NEWS,lang)
            latest_news.append({'cont':NEWS,'title': title, 'link': link, 'img_src': img_src,'ra' :read_more})
    
    def scrape_article(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            article_body = soup.find('div', class_='story-element story-element-text')
            if article_body:
                return article_body.get_text(strip=True)
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
        return None

    for news in latest_news:
        content = scrape_article(news['link'])
        news['content'] = translate_text(content, lang)
    
     
    return latest_news

def fetch_bbc_news(lang):
    url = 'https://www.bbc.com/news'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return []
    except Exception as err:
        print(f'Other error occurred: {err}')
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    news_section = soup.find_all('div', class_='sc-35aa3a40-2 cVXNac')
    
    latest_news = []
    base_url = 'https://www.bbc.com'
    for news in news_section:
        title_tag = news.find('h2',class_ ='sc-4fedabc7-3 zTZri')
        link_tag = news.find('a', class_='sc-2e6baa30-0 gILusN')
        img_tag = news.find('img',class_='sc-814e9212-0 hIXOPW')
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            link = link_tag['href']
            print(link)
            img_src = img_tag['src'] if img_tag else 'https://w7.pngwing.com/pngs/174/828/png-transparent-newspaper-animation-blackboard-newspaper-love-text-logo.png'
            if not link.startswith('http'):
                link = base_url + link
            title = translate_text(title,lang)
            cont = translate_text("GLOBAL NEWS",lang)
            latest_news.append({'cont':cont,'title': title, 'link': link, 'img_src': img_src})
            print(latest_news)
    def scrape_article(url):
      try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        
        paragraphs = soup.find_all('p', class_='sc-eb7bd5f6-0 fYAfXe')
        if not paragraphs:
            paragraphs = soup.find_all('p',class_='ssrcss-1q0x1qg-Paragraph e1jhz7w10')
        
        article_content = "".join([p.get_text(strip=True) for p in paragraphs])

        return article_content if article_content else None
      except Exception as e:
        print(f"Failed to scrape {url}: {e}")
      return None


    for news in latest_news:
        content = scrape_article(news['link'])
        print(news['link'])
        news['content'] = translate_text(content,lang)
    print(latest_news)
    
    return latest_news

@app.route('/')
def home_page():
    return render_template('start.html')

@app.route('/news', methods=['POST'])
def news():
    locality = request.form.get('locality')
    lang = request.form.get('language')
    print(locality, lang)
    if not locality:
        return "Please provide a locality.", 400

    local_news_data = fetch_latest_news(locality, lang)
    global_news_data = fetch_bbc_news(lang)
    return render_template('latest_news.html', news_data=local_news_data,global_news =global_news_data)
@app.route('/video')
def index():
    return render_template('video.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return "No file uploaded", 400

    video_file = request.files['video']
    target_language = request.form['language']
    
    # Save the uploaded video
    video_path = f"./static/uploads/{video_file.filename}"
    video_file.save(video_path)

    # Extract audio from video
    video_clip = mp.VideoFileClip(video_path)
    audio_path = "./static/uploads/temp_audio.wav"
    video_clip.audio.write_audiofile(audio_path)

    # Recognize speech and auto-detect language
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    
    detected_text = recognizer.recognize_google(audio, show_all=True)
    if not detected_text:
        return "No speech detected", 400
    
    # Get the most likely text and detected language
    best_alternative = detected_text['alternative'][0]
    text = best_alternative['transcript']
    
    print(detected_text)
    print(best_alternative, text)
    # Translate detected text to the target language
    translated_text = translate_text(text, target_language)
    
    # Convert translated text to speech
    tts = gTTS(translated_text, lang=target_language)
    translated_audio_path = f"./static/uploads/translated_audio.mp3"
    tts.save(translated_audio_path)

    # Return the HTML page with an audio player for the translated audio
    return render_template('play_audio.html', audio_file=translated_audio_path)

if __name__ == '__main__':
    app.run(debug=True)
