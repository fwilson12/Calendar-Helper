from openai import OpenAI

import datetime
import os.path
from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


from dotenv import load_dotenv
from pathlib import Path
import os

from vars import msg_history, system_prompt

SCOPES = ["https://www.googleapis.com/auth/calendar"]

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)


def get_service():
  creds = None
 
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    
    else:
      flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
      creds = flow.run_local_server(port=0)
    
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  
  return build("calendar", "v3", credentials=creds)



def create(summary, location, description, starttime, endtime, timezone):
  print("---TOOL CALL: CREATE EVENT---")
  service = get_service()
  event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': starttime,
            'timeZone': timezone,
            },
        'end': {
            'dateTime': endtime,
            'timeZone': timezone,
        },
        }
  event = service.events().insert(calendarId='primary', body=event).execute()
  #print( 'Event created: %s' % (event.get('htmlLink')))
  msg_history.append({"role": "system", "content": f"Event created: {event.get('htmlLink')}"})

def update(summary, location, description, starttime, endtime, timezone, event):
  service = get_service()
  pass

def readEvents(num_events, startime, endtime):
  print("---TOOL CALL: READ EVENTS - START: " + startime + " END: " + endtime + "---")
  try:
    service = get_service()

    # Call the Calendar API
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=startime,
            timeMax=endtime,
            maxResults=num_events,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      msg_history.append({"role": "system", "content": "No upcoming events found."})
      return

    
    msg = " "
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      msg += f"{start} {event['summary']}\n"
    
    msg_history.append({"role": "system", "content": msg})



  except HttpError as error:
    print(f"An error occurred: {error}")




def delete_event(title, day):
  print("---TOOL CALL: DELETE EVENT---")
  try:
    service = get_service()

    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin=day+'T00:00:00-05:00',
        timeMax=day+'T23:59:59-05:00',
        maxResults=30,
        singleEvents=True,
        orderBy="startTime",
      )
      .execute()
    )
    events = events_result.get("items", [])
    
    if not events:
      msg_history.append({"role": "system", "content": "No events found."})
      return
      
    name_id_list = []
    for event in events:
      name_id_list.append((event["summary"], event["id"]))

    # Convert the list of tuples to a string format that OpenAI can understand
    event_list_str = "\n".join([f"{name} -------> (id: {id})" for name, id in name_id_list])
    completion = client.chat.completions.create(
      model="gpt-5.1",
      store=True,
      messages=[
          {"role": "system", "content": """Given a list of event names and their corresponding IDs, find the ID of the event that matches 
          the provided title and return ONLY the ID."""},
          {"role": "user", "content": f"Event to delete: {title}\nAvailable events:\n{event_list_str}"}
      ]
    )

    id = completion.choices[0].message.content
  
    service.events().delete(calendarId='primary', eventId=id).execute()
    msg_history.append({"role": "assistant", "content": f"Deleted event with ID: {id}, title: {title}"})
    
 


  except HttpError as error:
    msg_history.append({"role": "system", "content": f"An error occurred: {error}"})
    print(f"An error occurred: {error}")
