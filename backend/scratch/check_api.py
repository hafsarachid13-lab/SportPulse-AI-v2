import requests
import json

def check_review_api():
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/review")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Review Structure Keys:", data.keys())
            if "sections" in data:
                print("Sections Keys:", data["sections"].keys())
                if "executive_summary" in data["sections"]:
                    print("Executive Summary found!")
                    print("Title:", data["sections"]["executive_summary"].get("title"))
                else:
                    print("Executive Summary NOT found in sections.")
            else:
                print("Sections NOT found in review data.")
        else:
            print("Error:", response.text)
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    check_review_api()
