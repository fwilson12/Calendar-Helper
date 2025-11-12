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

def update(summary, location, description, starttime, endtime, timezone, event):
  service = get_service()
  pass

def read10():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  try:
    service = get_service()

    # Call the Calendar API
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    msg = " "
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])
      msg += f"{start} {event['summary']}\n"
    
    msg_history.append({"role": "assistant", "content": msg})



  except HttpError as error:
    print(f"An error occurred: {error}")

def day_events(day):
  try:
    service = get_service()


    print("Getting events for "+day)
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
      print("No events found.")
      return

    # Prints the start and name of the events
    msg = "" 
    for event in events:
      start_str = event["start"].get("dateTime", event["start"].get("date"))
      start_dt = parser.parse(start_str)
      start_time = start_dt.strftime("%H:%M")
      print(start_time, event["summary"])
      msg += f"{start_time} {event['summary']}\n"
    msg_history.append({"role": "assistant", "content": msg})


  except HttpError as error:
    print(f"An error occurred: {error}")

def delete_event(title, day):

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
      print("No events on this day.")
      return
      
    name_id_list = []
    for event in events:
      name_id_list.append((event["summary"], event["id"]))

    # Convert the list of tuples to a string format that OpenAI can understand
    event_list_str = "\n".join([f"{name} -------> (id: {id})" for name, id in name_id_list])
    # print(event_list_str+'\n')
    completion = client.chat.completions.create(
      model="gpt-4o-mini",
      store=True,
      messages=[
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": f"Event to delete: {title}\nAvailable events:\n{event_list_str}"}
      ]
    )

    id = completion.choices[0].message.content
    #print('id: ', id)
    msg_history.append({"role": "assistant", "content": f"Deleted event with ID: {id}"})
    service.events().delete(calendarId='primary', eventId=id).execute()
    #print("Event deleted.")


  except HttpError as error:
    print(f"An error occurred: {error}")
