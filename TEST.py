import requests
from bs4 import BeautifulSoup

def fetch_bbc_news():
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
            img_src = img_tag['src'] if img_tag else ''
            if not link.startswith('http'):
                link = base_url + link
            latest_news.append({'title': title, 'link': link, 'img_src': img_src})
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
        news['content'] = content
    print(latest_news)
    return latest_news

fetch_bbc_news()