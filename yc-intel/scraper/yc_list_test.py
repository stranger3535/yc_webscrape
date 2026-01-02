import requests

BASE_URL = "https://www.ycombinator.com/companies"

def main():
    resp = requests.get(BASE_URL, timeout=10)
    print("Status code:", resp.status_code)
    with open("yc_companies_page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved to yc_companies_page.html")

if __name__ == "__main__":
    main()
