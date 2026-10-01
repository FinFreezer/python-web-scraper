import sys
from crawl import crawl_page

def main():
    argsLen = len(sys.argv)
    if argsLen < 2:
        #print("no website provided")
        sys.exit(1)
    if argsLen > 2:
        #print("too many arguments provided")
        sys.exit(1)
    #print(f"starting crawl of: {sys.argv[1]}")
    crawl_page(sys.argv[1])

if __name__ == "__main__":
    main()
