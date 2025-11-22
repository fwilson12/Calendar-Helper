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

from vars import msg_history

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
  try:
    event = service.events().insert(calendarId='primary', body=event).execute()
    return f"Event created: {event.get('htmlLink')}"

  except HttpError as error:
    msg_history.append({"role": "system", "content": f"An error occurred: {error}"})
    print(f"An error occurred: {error}")

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
    
    try:
      event = service.events().insert(calendarId='primary', body=event).execute()
      return f"Recurring event created: {event.get('htmlLink')}"

    except HttpError as error:
      msg_history.append({"role": "system", "content": f"An error occurred: {error}"})
      print(f"An error occurred: {error}")
      
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

    
    try:
      msg = " "
      for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        msg += f"{start} to {end}:  {event['summary']}\n"
      
      return "Retrieved events: \n" + msg
    
    except HttpError as error:
      msg_history.append({"role": "system", "content": f"Error processing events: {error}"})
      print(f"Error processing events: {error}")



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
      msg_history.append({"role": "tool", "content": "No events found."})
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
  
    try:
      service.events().delete(calendarId='primary', eventId=id).execute()
      return f"Deleted event with ID: {id}, title: {title}"
    
    except HttpError as error:
      msg_history.append({"role": "system", "content": f"Failed to delete event with ID: {id}, title: {title}. Error: {error}"})
      print(f"Failed to delete event with ID: {id}, title: {title}. Error: {error}")
      return
 


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
      msg_history.append({"role": "tool", "content": "No recurring series found."})
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

    
    try:
      service.events().delete(
      calendarId="primary",
      eventId=chosen_id
    ).execute()

      return f"Deleted recurring series with ID: {chosen_id}, title: {title}"
    
    except HttpError as error:
      msg_history.append({"role": "system", "content": f"Failed to delete recurring series with ID: {chosen_id}, title: {title}. Error: {error}"})
      print(f"Failed to delete recurring series with ID: {chosen_id}, title: {title}. Error: {error}")
      return

  except HttpError as error:
    msg_history.append({"role": "system", "content": f"An error occurred: {error}"})
    print(f"An error occurred: {error}")

def patch_event(title, starttime, endtime, patch_body, modify_series=False):
  print("---TOOL CALL: PATCH EVENT---")

  try:
    service = get_service()

    # Fetch events in the time window
    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin= "1000-01-01T00:00:00Z",  # far past
        timeMax=endtime,
        maxResults=999,
        singleEvents=True,
        orderBy="startTime",
      )
      .execute()
    )
    events = events_result.get("items", [])

    if not events:
      msg_history.append({"role": "tool", "content": "No events found to patch."})
      return

    # Build summary → id list for GPT selection (same as delete function)
    name_id_list = []
    for event in events:
      name = event.get("summary", "No Title")
      name_id_list.append((name, event["id"]))

    event_list_str = "\n".join([f"{name}, {event['start']} -------> (id: {id})" for name, id in name_id_list])

    # Ask GPT to match the correct event ID like your delete flow
    completion = client.chat.completions.create(
      model="gpt-5.1",
      store=True,
      messages=[
        {"role": "system", "content": f"""Modify_Seires: {modify_series} | Given a list of event names and their corresponding IDs, 
        return ONLY the ID of the event that matches the provided title pick the first event of the recurring series to patch if modify recurring is true."""},
        {"role": "user", "content": f"Event to patch: {title}\nAvailable events:\n{event_list_str}"}
      ]
    )

    target_id = completion.choices[0].message.content

    # Determine if this event is part of a recurring series
    # Fetch the event details so we can check fields
    event_obj = service.events().get(calendarId="primary", eventId=target_id).execute()

    if "recurringEventId" in event_obj:
      # It's an instance of a series
      if modify_series:
        patch_id = event_obj["recurringEventId"]   # patch the entire series
      else:
        patch_id = target_id                       # patch only this instance
   
    else:
      patch_id = target_id                            # normal single event

    # Perform the patch
    try:
      service.events().patch(
        calendarId="primary",
        eventId=patch_id,
        body=patch_body
    ).execute()

      if patch_body is None or patch_body == {}:
        return "patch body was left blank. no changes were made"
        
      else:
        return f"Patched event '{title}' (id: {patch_id}) with these changes: {patch_body}."

    
    except HttpError as error:
      msg_history.append({"role": "system", "content": f"Failed to patch event '{title}' (id: {patch_id}): {error}"})
      print(f"Failed to patch event '{title}' (id: {patch_id}): {error}")
      return
    
  except Exception as error:
    msg_history.append({"role": "system", "content": f"Patch failed: {error}"})
    print(f"Patch failed: {error}")
    return
