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
    # Modern, comic-themed styling
    email_body = """
    <html>
    <head>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0d0221;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 800px;
                margin: 20px auto;
                background-color: #1a0b2e;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(138, 43, 226, 0.3);
                overflow: hidden;
                position: relative;
            }
            .container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-image: 
                    radial-gradient(2px 2px at 20% 30%, white, transparent),
                    radial-gradient(2px 2px at 60% 70%, #b388ff, transparent),
                    radial-gradient(1px 1px at 50% 50%, #8a2be2, transparent),
                    radial-gradient(1px 1px at 80% 10%, #e0b3ff, transparent),
                    radial-gradient(2px 2px at 90% 60%, #c77dff, transparent),
                    radial-gradient(1px 1px at 15% 90%, white, transparent),
                    radial-gradient(1px 1px at 40% 20%, #9d4edd, transparent),
                    radial-gradient(2px 2px at 70% 85%, white, transparent),
                    radial-gradient(1px 1px at 25% 60%, #b388ff, transparent),
                    radial-gradient(1px 1px at 85% 40%, #e0b3ff, transparent);
                background-size: 200% 200%;
                background-position: 0% 0%;
                pointer-events: none;
                opacity: 0.6;
                z-index: 1;
            }
            .header {
                background: linear-gradient(135deg, #3c0f70 0%, #1a0033 100%);
                color: #ffffff;
                padding: 30px;
                text-align: center;
                position: relative;
                z-index: 2;
            }
            .header h1 {
                margin: 0;
                font-size: 28px;
                text-shadow: 0 1px 0 #c77dff, 0 2px 0 #9d4edd, 0 3px 0 #7b2cbf, 0 4px 5px rgba(0,0,0,0.5);
                color: #e0b3ff;
                background: linear-gradient(to bottom, #ffffff 0%, #e0b3ff 50%, #b388ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .content {
                padding: 30px;
                position: relative;
                z-index: 2;
            }
            .volume-section {
                margin-bottom: 30px;
                border-left: 4px solid #8a2be2;
                padding-left: 20px;
            }
            .volume-title {
                color: #ffffff;
                font-size: 22px;
                margin-bottom: 15px;
                font-weight: bold;
                text-shadow: 0 1px 0 #9d4edd, 0 2px 0 #7b2cbf, 0 3px 3px rgba(0,0,0,0.4);
                background: linear-gradient(to bottom, #ffffff 0%, #e0b3ff 40%, #b388ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .comic-item {
                background-color: #16213e;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                box-shadow: 0 4px 12px rgba(138, 43, 226, 0.2);
                transition: transform 0.2s;
                border: 1px solid #2d1b69;
            }
            .comic-item:hover {
                transform: translateX(5px);
            }
            .comic-image {
                max-width: 120px;
                height: auto;
                border-radius: 5px;
                margin-right: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                position: relative;
                z-index: 1;
            }
            .comic-details {
                flex: 1;
                position: relative;
                z-index: 1;
            }
            .issue-number {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
                text-shadow: 0 1px 0 #c77dff, 0 2px 2px rgba(0,0,0,0.3);
                background: linear-gradient(to bottom, #ffffff 0%, #e0b3ff 50%, #c77dff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .release-date {
                color: #d4d4d4;
                font-size: 14px;
            }
            .footer {
                background-color: #0d0221;
                padding: 20px;
                text-align: center;
                color: #a0a0a0;
                font-size: 12px;
            }
            .no-comics {
                text-align: center;
                padding: 40px;
                color: #d4d4d4;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Here are the new Marvel & DC comics for this week:</h1>
            </div>
            <div class="content">
    """
    
    if not comics:
        email_body += '<div class="no-comics"><p>No new comics this week.</p></div>'
    else:
        # Sort comics by volume name
        comics_by_volume = {}
        for comic in comics:
            volume = comic["name"]
            if volume not in comics_by_volume:
                comics_by_volume[volume] = []
            comics_by_volume[volume].append(comic)
        
        # Add sorted volumes to email with enhanced styling
        for volume_name in sorted(comics_by_volume.keys()):
            email_body += f'<div class="volume-section">\n'
            email_body += f'<div class="volume-title">{volume_name}</div>\n'
            
            for comic in comics_by_volume[volume_name]:
                email_body += '<div class="comic-item">\n'
                
                if comic.get("image_url"):
                    email_body += f'<img src="{comic["image_url"]}" class="comic-image" alt="{volume_name} cover" />\n'
                
                email_body += '<div class="comic-details">\n'
                email_body += f'<div class="issue-number">Issue #{comic["issue_number"]}</div>\n'
                email_body += f'<div class="release-date">Release Date: {comic["cover_date"]}</div>\n'
                email_body += '</div>\n'
                email_body += '</div>\n'
            
            email_body += '</div>\n'
    
    email_body += """
            </div>
            <div class="footer">
                Powered by Comic Vine API
            </div>
        </div>
    </body>
    </html>
    """
    
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