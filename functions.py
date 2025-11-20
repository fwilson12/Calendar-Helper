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
        }       
        }
  event = service.events().insert(calendarId='primary', body=event).execute()
  #print( 'Event created: %s' % (event.get('htmlLink')))
  msg_history.append({"role": "system", "content": f"Event created: {event.get('htmlLink')}"})




def create_recurring(
    summary,
    location,
    description,
    starttime,
    endtime,
    timezone,
    frequency,                 # DAILY, WEEKLY, MONTHLY, YEARLY
    interval=1,                # every N units
    weekdays=None,             # ["MO","WE","FR"]
    monthday=None,             # e.g. 15 for 15th of each month
    nth_weekday=None,          # {"weekday": "TU", "nth": 1}
    until=None,                # "YYYYMMDDT000000Z"
    count=None,                # integer
    exception_dates=None       # ["20250110T090000Z", ...]
):
    print("---TOOL CALL: CREATE RECURRING EVENT---")
    service = get_service()

    # ---------------------------
    # Build RRULE
    # ---------------------------
    rrule_parts = [f"FREQ={frequency.upper()}"]

    if interval:
        rrule_parts.append(f"INTERVAL={interval}")

    # Weekly patterns: BYDAY=MO,WE,FR
    if weekdays:
        byday = ",".join(weekdays)
        rrule_parts.append(f"BYDAY={byday}")

    # Simple monthly: BYMONTHDAY=15
    if monthday:
        rrule_parts.append(f"BYMONTHDAY={monthday}")

    # Advanced monthly: BYDAY=1TU (1st Tue), -1MO (last Mon)
    if nth_weekday:
        nth = nth_weekday.get("nth")
        weekday = nth_weekday.get("weekday")
        rrule_parts.append(f"BYDAY={nth}{weekday}")

    if until:
        rrule_parts.append(f"UNTIL={until}")

    if count:
        rrule_parts.append(f"COUNT={count}")

    rrule_string = ";".join(rrule_parts)

    # ---------------------------
    # Build EXDATE list (if any)
    # ---------------------------
    exdate_block = None
    if exception_dates:
        # Google requires: "EXDATE:20250110T090000Z,20250115T090000Z"
        exdate_block = ",".join(exception_dates)

    # ---------------------------
    # Build Event Body
    # ---------------------------
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
        'recurrence': [
            f"RRULE:{rrule_string}"
        ]
    }

    if exdate_block:
        event["recurrence"].append(f"EXDATE:{exdate_block}")

    # ---------------------------
    # Send to Google Calendar
    # ---------------------------
    event = service.events().insert(calendarId='primary', body=event).execute()

    msg_history.append({
        "role": "system",
        "content": f"Recurring event created: {event.get('htmlLink')}"
    })


def update(summary, location, description, starttime, endtime, timezone, event):
  service = get_service()
  pass

def readEvents(num_events, starttime, endtime):
  print("---TOOL CALL: READ EVENTS - START: " + starttime + " END: " + endtime + "---")
  try:
    service = get_service()

    # Call the Calendar API
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=starttime,
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




def delete_event(title, starttime, endtime):

  print("---TOOL CALL: DELETE EVENT---")
  
  try:
    service = get_service()

    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin=starttime,
        timeMax=endtime,
        maxResults=999,
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




def delete_recurring(title, starttime, endtime):

  print("---TOOL CALL: DELETE RECURRING SERIES---")

  try:
    service = get_service()

    # Retrieve recurring masters (singleEvents=False)
    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin=starttime,
        timeMax=endtime,
        maxResults=999,
        singleEvents=False, # <--- key
        )
        .execute()
      )

    events = events_result.get("items", [])

    # Filter to only recurring *series masters*
    recurring_masters = [
      event for event in events
      if event.get("recurrence") and not event.get("recurringEventId")
    ]

    if not recurring_masters:
      msg_history.append({"role": "system", "content": "No recurring series found."})
      return

    name_id_list = []
    for event in recurring_masters:
      summary = event["summary"]
      event_id = event["id"]
      name_id_list.append((summary, event_id))

    event_list_str = "\n".join([
      f"{name} -------> (id: {id})"
      for name, id in name_id_list
    ])

    completion = client.chat.completions.create(
      model="gpt-5.1",
      store=True,
      messages=[
        {"role": "system", "content": """Given a list of recurring event series names and their IDs, return ONLY the ID of the series 
        that best matches the provided title. Return ONLY the ID."""},
        {"role": "user", "content": f"Recurring series to delete: {title} \nAvailable series:\n{event_list_str}"}
      ]
    )

    chosen_id = completion.choices[0].message.content

    
    service.events().delete(
      calendarId="primary",
      eventId=chosen_id
    ).execute()

    msg_history.append({
      "role": "assistant",
      "content": f"Deleted recurring series with ID: {chosen_id}, title: {title}"
    })

  except HttpError as error:
    msg_history.append({"role": "system", "content": f"An error occurred: {error}"})
    print(f"An error occurred: {error}")
