import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

from config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def get_youtube_client():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickel', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        # Load the flow from the client secrets
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', scopes)
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        logger.debug(f"\n🚀 Visit this URL to authorize:\n{auth_url}\n")
        
        code = input("Enter the code from the browser: ").strip()
        flow.fetch_token(code=code)
        creds = flow.credentials

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    logger.info("YouTube client authenticated successfully.")
    return build("youtube", "v3", credentials=creds)

def upload_video(file_path, title):
    youtube = get_youtube_client()
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title, 
                "description": "The history they didn't want you to know. One fact a day from The Professor.",
                "tags": ["#Shorts", "#History", "#Facts", "#DidYouKnow", "#Educational", "#HistoryBuff"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )
    logger.info("Uploading...")
    response = request.execute()
    logger.info(f"Success! Video ID: {response['id']}")