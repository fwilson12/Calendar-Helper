from openai import OpenAI
import json 

import datetime
import os.path
from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/calendar"]


client = OpenAI(
  api_key="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"
)


def create(summary, location, description, starttime, endtime, timezone):
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  
  service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
  now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

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
  print( 'Event created: %s' % (event.get('htmlLink')))

# def delete():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  
  service = build("calendar", "v3", credentials=creds)

def read10():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

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
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")



def day_events(day):

  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
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
    for event in events:
      start_str = event["start"].get("dateTime", event["start"].get("date"))
      start_dt = parser.parse(start_str)
      start_time = start_dt.strftime("%H:%M")
      print(start_time, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")


def chat():
  function_spec = [
    {
        "name": "create",
        "description": "Create a Google Calendar meeting with given details",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "title(called summary) of the meeting"},
                "location": {"type": "string", "description": "Location of the meeting"},
                "description": {"type": "string", "description": "Description of the meeting"},
                "starttime": {"type": "string", "description": "Start time in ISO 8601 format"},
                "endtime": {"type": "string", "description": "End time in ISO 8601 format"},
                "timezone": {"type": "string", "description": "Timezone of the event (usually 'America/Chicago')"},
            },
            "required": ["summary", 'location', "description", "starttime", "endtime", "timezone"],
        },
    },
    {
      "name": "read10",
      "description": "returns the user's next 10 events on their calendar"
    },
    {
      "name": "day_events",
      "description": "returns all events for a given day",
      "parameters": {
        "type": "object",
        "properties": {
          "day": {"type": "string", "description": "the DTF of the given day without time. For example, may 24th would be 2025-05-24"}
        }
      }
    }

    ]

  str = input("Hello, how may I assist you today?")
  
  completion = client.chat.completions.create(
    model="gpt-4o-mini",
    store=True,
    messages=[
      {"role": "system", "content": "You are a google calendar automation assistant that will make an appropriate api call "
      "depending on the user's request. Be very concise and professional with your messages. You will be given a summary, location, description, "
      "starttime, endtime, and timezone to input in that order to a python function called 'create', which takes in all of those attributes as strings. You have access to call this function."
      "assume the timezone is Chicago for the last attribute after endtime, and use the dateTime format, e.g. '2025-04-30T05:00:00-05:00' for the start and end times."
      "return the appropriate function call with your message. You also have the ability to call the 'read10()' function that returns the user's next 10 events, make sure you call that "
      "function if you deem the user is asking for their upcoming events. Also, you have the access to the 'day_events(day)' function, where day is the user's requested day in "
      "date-time format without time included."
      ""},
      {"role": "user", "content": str} 
    ],
    tools=[
        {
            "type": "function",
            "function": function_spec[0]
        },
        {
          "type": "function",
          "function": function_spec[1]
        },
        {
          "type": "function",
          "function": function_spec[2]
        }

    ],
    tool_choice="auto"
  )

  message = (completion.choices[0].message)
  # print(message)


  if message.tool_calls is not None:
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    if function_name == "create":
      create(
        summary=function_args.get('summary', ''),
        location=function_args.get('location', ''),
        description=function_args.get('description', ''),
        starttime=function_args.get('starttime'),
        endtime=function_args.get('endtime'),
        timezone=function_args.get('timezone')
            )
      
    elif function_name == "read10":
      read10()

    elif function_name == 'day_events':
      day_events(day=function_args.get('day'))

  else:
    print(message.content)

chat()