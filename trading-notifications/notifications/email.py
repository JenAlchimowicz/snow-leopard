import boto3
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def send_update_email(tickers: list[str], recipients: list[str]) -> None:
    AWS_REGION = "eu-west-1"
    SENDER = "snow-leopard@mlprojectsbyjen.com"
    SUBJECT = "Snow Leopard Detected"
    
    # 1. Setup the Container
    msg = MIMEMultipart('related')
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = ", ".join(recipients)

    # 2. Build the HTML and find valid images first
    today_str = datetime.now().strftime("%Y-%m-%d")
    html_sections = [f"<h2>Snow Leopard Detection - {today_str}</h2>"]
    valid_images = [] # Store (path, cid) to attach later

    for ticker in tickers:
        html_sections.append(f"<p><b>Ticker: {ticker}</b></p>")
        
        # Replace this with your actual Config.RESOURCES_PATH
        image_path = f"./resources/{ticker}.png" 
        
        if os.path.exists(image_path):
            cid_name = f"img_{ticker}"
            html_sections.append(f'<div><img src="cid:{cid_name}" style="max-width:600px; border:1px solid #eee;"></div>')
            valid_images.append((image_path, cid_name))
        else:
            html_sections.append(f"<p style='color:gray;'><i>(No graph found for {ticker})</i></p>")

    # 3. ATTACH HTML FIRST
    # This ensures the email client loads the structure before the data
    full_html = f"<html><body>{''.join(html_sections)}</body></html>"
    msg.attach(MIMEText(full_html, 'html'))

    # 4. ATTACH IMAGES SECOND
    for img_path, cid in valid_images:
        try:
            with open(img_path, 'rb') as f:
                img_data = f.read()
            msg_img = MIMEImage(img_data)
            msg_img.add_header('Content-ID', f'<{cid}>')
            msg_img.add_header('Content-Disposition', 'inline')
            msg.attach(msg_img)
        except Exception as e:
            print(f"Could not attach {img_path}: {e}")

    # 5. SEND
    client = boto3.client('ses', region_name=AWS_REGION)
    try:
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=recipients,
            RawMessage={'Data': msg.as_string()}
        )
        print(f"Success! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error: {e}")