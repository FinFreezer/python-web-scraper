from urllib.parse import urlsplit
from urllib.parse import urljoin
from typing import TypedDict, NotRequired
import requests
import asyncio
import aiohttp
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

class AsyncCrawler():
    def __init__(self, base_url: str, max_concurrency: int, max_pages: int):
        self.base_url: str = base_url
        self.base_domain: str = urlsplit(base_url).netloc
        self.page_data: Page_data = {}
        self.visited: set[str] = set()
        self.lock = asyncio.Lock()
        self.max_concurrency: int = max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session: aiohttp.ClientSession | None = None
        self.max_pages: int = max_pages
        self.should_stop: bool = False
        self.all_tasks: set[asyncio.Task[None]] = set()

    async def __aenter__(self) -> "AsyncCrawler":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: BaseException | None) -> None:
        if self.session is not None:
            await self.session.close()

    async def add_page_visit(self, normalized_url) -> bool:
        if self.should_stop:
            return False
        if len(self.visited) >= self.max_pages:
            self.should_stop = True
            print("Reached maximum number of pages to crawl.")
            return False
        async with self.lock:
            if normalized_url in self.visited:
                return False
            self.visited.add(normalized_url)
            return True
        
    async def get_html(self, url: str) -> str:
        if self.session is None:
            return
        try:
            async with self.session.get(url) as resp:
                print(f"Making a requst to {url}")
                #r = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
                if 399 < resp.status < 500:
                    raise PermissionError
                header = resp.headers.get("Content-Type")
                text = await resp.text()
                if header == None or not "text/html" in header:
                    raise ValueError
                if text == "":
                    raise ValueError
                return text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        
    async def crawl_page(self, current_url: str = None):
        if self.should_stop:
            return
        if current_url == None:
            current_url = self.base_url
        if not await self.add_page_visit(current_url):
            return
        #print(f"Comparing {url} to {normalize_url(base_url)}")
        if not checkLinkBounds(current_url, self.base_url):
            return
        async with self.semaphore:
            #print(f"Getting HTML from {current_url}")
            html = await self.get_html(current_url)
            if html is None:
                return
            data: Extracted_data = extract_page_data(html, current_url)
            async with self.lock:
                self.page_data[normalize_url(current_url)] = data
        #print(data["outgoing_links"])
        if self.should_stop:
            return

        tasks: list[asyncio.Task[None]] = []
        for link in data["outgoing_links"]:
            #input(f"[{link}] press Enter to continue...")
            task = asyncio.create_task(self.crawl_page(link))
            tasks.append(task)
            self.all_tasks.add(task)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                for task in tasks:
                    self.all_tasks.discard(task)
            
    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data

def normalize_url(url: str) -> str:
    parsed_url = urlsplit(url)
    full_path = f"{parsed_url.netloc}{parsed_url.path}"
    full_path = full_path.rstrip("/")
    #print(f"Transformed {url} to {full_path}")
    return full_path.lower()

def checkLinkBounds(url, base_url) -> bool:
    root = urlsplit(base_url)
    child = urlsplit(url)
    if root.netloc == child.netloc:
        return True
    return False

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
        href = link.get('href')
        if href[-1] == "/":
            href = href[0:-1]
        if href is None:
            continue
        #print(f"Found href: {href} on page {base_url}.")
        if href in base_url:
            continue
        if href[0] == "/":
            fullURL = urljoin(base_url, href)
            if not fullURL in URLs:
                #print(f"Appending short URL {fullURL} to URLs.")
                URLs.append(fullURL)
        elif href not in URLs:
            #print(f"Appending long URL {href} to URLs.")
            URLs.append(href)
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
    #print(f"Extracting data from {page_url}")
    heading = get_heading_from_html(html)
    first_paragraph = get_first_paragraph_from_html(html)
    outgoing_links = get_urls_from_html(html, page_url)
    image_urls = get_images_from_html(html, page_url)
    data: Extracted_data = {
        "url": page_url, 
        "heading": heading, 
        "first_paragraph": first_paragraph, 
        "outgoing_links": outgoing_links, 
        "image_urls": image_urls,
    }
    return data

async def crawl_site_async(base_url: str, max_concurrent: int, max_pages: int) -> Page_data:
    async with AsyncCrawler(base_url, max_concurrent, max_pages) as crawler:
        page_data = await crawler.crawl()
        return page_data