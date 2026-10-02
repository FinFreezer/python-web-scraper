import json

def write_json_report(page_data, filename="report.json"):
    pages_list = []
    for page in page_data.values():
        print(f"Adding {page["url"]} to pages_list.")
        pages_list.append(page)
    pages_list = sorted(pages_list, key=lambda p: p["url"])
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(pages_list, file, indent=2)
    return