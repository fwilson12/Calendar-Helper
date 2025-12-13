from config import app, db 
from flask import request, jsonify

from functions import create, create_recurring, readEvents, delete_event, delete_recurring, patch_event
from vars import msg_history, summary_prompt, TOOLS

from openai import OpenAI
import json

from dotenv import load_dotenv
from pathlib import Path
import os

from main import tool_call, chat


SCOPES = ["https://www.googleapis.com/auth/calendar"]


env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)






if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    
    app.run(debug=True)