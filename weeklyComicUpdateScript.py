import requests
import datetime 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(__file__), "configs.env"))

# -- Configuration --
COMIC_API_KEY = os.getenv("COMIC_API_KEY")
if not COMIC_API_KEY:
    print("Error: COMIC_API_KEY not found in configs.env")
    raise RuntimeError("COMIC_API_KEY is required")

#SMTP configuration
SMTP_SERVER = "smtp.mailgun.org"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
if not SMTP_PASSWORD:
    print("Error: EMAIL_PASSWORD not found in configs.env")
    raise RuntimeError("EMAIL_PASSWORD is required")

FROM = "comic-bot@RamSoftware"
TO_EMAIL = "aidenramos901@gmail.com"
#--------------------------


#the days to get the comics for
def get_week():
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=7)
    return start_of_week, today

#getting the comics for the week
def get_comics():
    headers = {"User-Agent": "weekly-comic-script/1.0"}
    start,end= get_week()

    url="https://comicvine.gamespot.com/api/issues/"

    all_results = []
    offset = 0
    max_results = 10000
    limit = 100
    
    
    while len(all_results) < max_results:
        params={
            "api_key": COMIC_API_KEY,
            "format":"json",
            "filter":f"cover_date:{start}|{end}",
            "limit":limit,
            "offset":offset}
        
        # calling the API
        try:
            response=requests.get(url, params=params, headers=headers, timeout=10)
            try:
                response.raise_for_status()
            except requests.HTTPError as http_err:
                print(f"API HTTP error {response.status_code}: {http_err}\nBody: {response.text}")
                break

            data=response.json()
        except requests.RequestException as e:
            print(f"Error fetching data from API: {e}")
            break
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            break

        if "results" not in data or not data["results"]:
            break
        
        all_results.extend(data["results"])
        offset += limit
        
        # Stop if 've reached the total available or  max
        total_available = data.get("number_of_total_results", len(all_results))
        if len(all_results) >= total_available or len(all_results) >= max_results:
            break
    
    print(f"API returned {len(all_results)} total issues")
    results = all_results
    
    comics=[]
    #  Marvel and DC identifiers
    marvel_dc_keywords = ["marvel", "dc comics", "batman", "superman", "spider-man", "x-men", "avengers", "fantastic four", "green lantern", "wonder woman", "flash", "captain america","magik","moon knight","wolverine"]
    
    for issue in results:
        try:
            # Safe nested access
            volume = issue.get("volume", {})
            if not volume or not isinstance(volume, dict):
                continue
            
            name = volume.get("name", "Unknown")
            
            # Filter by Marvel/DC keywords
            if not any(keyword.lower() in name.lower() for keyword in marvel_dc_keywords):
                continue
            
            issue_number = issue.get("issue_number", "N/A")
            cover_date = issue.get("cover_date", "N/A")
            publisher = "Marvel/DC"  #  Marvel or DC based filter
            
            # Get cover image URL
            image = issue.get("image", {})
            image_url = None
            if isinstance(image, dict):
                image_url = image.get("medium_url") or image.get("screen_url") or image.get("original_url")
            
            comics.append({
                "name": name,
                "issue_number": issue_number,
                "cover_date": cover_date,
                "publisher": publisher,
                "image_url": image_url
            })
        except Exception as e:
            print(f"Error parsing issue: {e}")
            continue
    
    print(f"Parsed {len(comics)} Marvel/DC comics")
    return comics


def format_email(comics):

    email_body = "<h2>Here are the new Marvel & DC comics for this week:</h2>\n\n"
    
    if not comics:
        email_body+= "<p>No new comics this week.</p>"
        return email_body

    # Sort comics by volume name
    comics_by_volume = {}
    for comic in comics:
        volume = comic["name"]
        if volume not in comics_by_volume:
            comics_by_volume[volume] = []
        comics_by_volume[volume].append(comic)
    
    # Add sorted volumes to email with cover images
    for volume_name in sorted(comics_by_volume.keys()):
        email_body += f"<h3>{volume_name}</h3>\n"
        for comic in comics_by_volume[volume_name]:
            image_html = ""
            if comic.get("image_url"):
                image_html = f'<img src="{comic["image_url"]}" style="max-width: 150px; margin: 10px 0;" /><br/>'
            
            email_body += f"<div style='margin-bottom: 20px;'>"
            email_body += image_html
            email_body += f"<strong>Issue #{comic['issue_number']}</strong> - Release Date: {comic['cover_date']}"
            email_body += f"</div>\n"
            email_body += "<hr style='border: 1px solid #ccc; margin: 15px 0;'/>\n"

    return email_body
    
def send_email(subject, body):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = FROM
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM, TO_EMAIL, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    #getting the comics for the week
    comics = get_comics()
    #formatting the email body
    email_body = format_email(comics)
    #sending the email
    send_email("Weekly Comic Book Releases", email_body)

if __name__ == "__main__":
    main()