import sys
from crawl import crawl_site_async
from json_report import write_json_report
import asyncio

async def main():
    argsLen = len(sys.argv)
    if argsLen < 4:
        print("usage python main.py <base_url> <max_concurrency> <max_pages>")
        sys.exit(1)
    if argsLen > 4:
        print("too many arguments provided")
        sys.exit(1)
    print(f"starting crawl of: {sys.argv[1]}")
    if not sys.argv[2].isdigit():
        print("max_concurrency must be an integer")
        sys.exit(1)
    if not sys.argv[3].isdigit():
        print("max_pages must be an integer")
        sys.exit(1)
    max_concurrent: int = int(sys.argv[2])
    max_pages: int = int(sys.argv[3])
    page_data = await crawl_site_async(sys.argv[1], max_concurrent, max_pages)
    #for page in page_data.values():
        #print(f"Found {len(page['outgoing_links'])} outgoing links on {page['url']}")
    write_json_report(page_data)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
