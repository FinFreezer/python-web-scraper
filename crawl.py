from urllib.parse import urlsplit
from urllib.parse import urljoin
from typing import TypedDict, NotRequired
import requests
from bs4 import BeautifulSoup, Tag

class Extracted_data(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

class Page_data(TypedDict):
    url: str
    data: Extracted_data

def normalize_url(url: str) -> str:
    fields = urlsplit(url)
    path = fields.path
    baseURL = fields.netloc
    if baseURL[:3] != "www":
        baseURL = "www." + baseURL
    if path != "" and path[-1] == "/":
       path = path[0:-1]
    return baseURL + path

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.h1
    if heading == None:
        heading = soup.h2
        if heading == None:
            return ""
    return heading.get_text()

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    paragraph = None
    if soup.main != None and soup.main.p != None:
        paragraph = soup.main.p
    if paragraph == None:
        paragraph = soup.p
        if paragraph == None:
            return ""
    return paragraph.get_text()

def get_urls_from_html(html: str, base_url: str) -> list[str]:
    #print(f"Scraping for URLs from {base_url}")
    soup = BeautifulSoup(html, 'html.parser')
    URLs: list[str] = []
    for link in soup.find_all('a'):
        if link == base_url:
            continue
        if link.get('href') != "" and link.get('href')[0] == "/":
            fullURL = urljoin("https://" + base_url, link.get('href'))
            if not fullURL in URLs:
                #print(f"Appending short URL {fullURL} to URLs.")
                URLs.append(fullURL)
        elif link.get('href') != "":
            if not link.get('href'):
                URLs.append(link.get('href'))
                #print(f"Appending long URL {link.get('href')} to URLs.")
    
    return URLs

def get_images_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    images: list[str] = []
    for link in soup.find_all('img'):
        if link.get('src') != "" and link.get('src')[0] == "/":
            fullURL = urljoin(base_url, link.get('src'))
            images.append(fullURL)
        elif link.get('src') != "":
            images.append(link.get('src'))
    return images

def extract_page_data(html: str, page_url: str) -> Extracted_data:
    print(f"Extracting data from {page_url}")
    url = page_url
    heading = get_heading_from_html(html)
    first_paragraph = get_first_paragraph_from_html(html)
    outgoing_links = get_urls_from_html(html, page_url)
    image_urls = get_images_from_html(html, page_url)
    data: Extracted_data = {
        "url": url, 
        "heading": heading, 
        "first_paragraph": first_paragraph, 
        "outgoing_links": outgoing_links, 
        "image_urls": image_urls,
    }
    return data

def get_html(url: str) -> str:
    print(f"Making a requst to {url}\n")
    r = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    if 399 < r.status_code < 500:
        raise PermissionError
    if not "text/html" in r.headers.get("Content-Type"):
        raise ValueError
    if r.text == "":
        raise ValueError
    return r.text

def crawl_page(base_url: str, current_url: str = None, page_data: Page_data = None):
    if current_url == None:
        current_url = base_url
    url = normalize_url(current_url)
    if not normalize_url(base_url) in url:
        return
    if page_data == None:
        page_data: Page_data = {}
    if url in page_data.keys():
        return
    html = get_html("https://" + url)
    #print(html)
    data: Extracted_data = extract_page_data(html, url)
    page_data.update({"url": url, "data": data})
    #print(data["outgoing_links"])
    print(data["outgoing_links"])
    for link in data["outgoing_links"]:
        #input(f"[{link}] press Enter to continue...")
        crawl_page(base_url, link, page_data)
    return