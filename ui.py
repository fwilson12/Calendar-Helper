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


from dotenv import load_dotenv
from pathlib import Path
import os


SCOPES = ["https://www.googleapis.com/auth/calendar"]




env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# print(OPENAI_API_KEY)



client = OpenAI(api_key= OPENAI_API_KEY)


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

def update(summary, location, description, starttime, endtime, timezone, event):
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

def read10():
    """Returns the start and name of the next 10 events on the user's calendar.
    
    Returns:
        str: Formatted string containing the next 10 events
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
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
            return "No upcoming events found."

        # Format each event with HTML for better spacing
        result = ["<div style='margin-bottom: 15px;'><b>Your next 10 events:</b></div>"]
        
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            try:
                # Format the date/time nicely
                start_dt = parser.parse(start)
                if "T" in start:  # It's a datetime with time
                    date_str = start_dt.strftime("%a, %b %d")
                    time_str = start_dt.strftime("%I:%M %p").lstrip('0')
                    start_str = f"{date_str} at {time_str}"
                else:  # It's just a date
                    start_str = start_dt.strftime("%a, %b %d, %Y")
            except:
                start_str = str(start)
            
            # Build the event HTML
            event_html = []
            event_html.append(f"<div style='font-weight: 500;'>{event['summary']}</div>")
            event_html.append(f"<div style='margin-left: 15px; color: #555;'>📅 {start_str}</div>")
            
            if "location" in event and event["location"]:
                event_html.append(f"<div style='margin-left: 15px; color: #555;'>📍 {event['location']}</div>")
            
            # Add the event to results with a separator line
            result.append("".join(event_html))
            result.append("<div style='color: #e0e0e0; margin: 10px 0;'>________________________________________</div>")
            result.append("")  # Empty line for spacing

        return "\n".join(result)

    except HttpError as error:
        return f"An error occurred: {error}"

def day_events(day):
    """Returns all events for a specific day.
    
    Args:
        day (str): The date in YYYY-MM-DD format
        
    Returns:
        str: Formatted string containing the events for the day
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
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

        # Format the day for display
        try:
            day_dt = parser.parse(day)
            day_display = day_dt.strftime("%A, %B %d, %Y")
        except:
            day_display = day

        # Call the Calendar API
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
            return f"No events found for {day_display}."

        # Format each event with HTML for better spacing
        result = [f"<div style='margin-bottom: 15px;'><b>Events for {day_display}:</b></div>"]
        
        for event in events:
            start_str = event["start"].get("dateTime", event["start"].get("date"))
            
            # Build the event HTML
            event_html = []
            
            try:
                start_dt = parser.parse(start_str)
                if "T" in start_str:  # It's a datetime with time
                    time_str = start_dt.strftime("%I:%M %p").lstrip('0')
                    event_html.append(f"<div style='font-weight: 500;'>{event['summary']}</div>")
                    event_html.append(f"<div style='margin-left: 15px; color: #555;'>🕒 {time_str}</div>")
                else:  # It's an all-day event
                    event_html.append(f"<div style='font-weight: 500;'>{event['summary']} (All day)</div>")
            except:
                event_html.append(f"<div style='font-weight: 500;'>{event['summary']}</div>")
            
            # Add event details
            if "location" in event and event["location"]:
                event_html.append(f"<div style='margin-left: 15px; color: #555;'>📍 {event['location']}</div>")
            
            if "description" in event and event["description"]:
                desc = event["description"].replace("\n", " ")
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                event_html.append(f"<div style='margin-left: 15px; color: #555;'>📝 {desc}</div>")
            
            # Add the event to results with a separator line
            result.append("".join(event_html))
            result.append("<div style='color: #e0e0e0; margin: 10px 0;'>________________________________________</div>")
            result.append("")  # Empty line for spacing

        return "\n".join(result)

    except HttpError as error:
        return f"An error occurred: {error}"

def delete_event(title, day):
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
            {"role": "system", "content": "You will be given a title of an event on a google calendar, and a list of event titles with an associated id string for that day. Your job is to pick which event the user is referring to, and return ONLY the id string of that event"},
            {"role": "user", "content": f"Event to delete: {title}\nAvailable events:\n{event_list_str}"}
        ]
    )

    id = completion.choices[0].message.content
    print('id: ', id)
    service.events().delete(calendarId='primary', eventId=id).execute()
    print("Event deleted.")


  except HttpError as error:
    print(f"An error occurred: {error}")






def chat(user_input, callback):
    """Process user input and return response through callback
    
    Args:
        user_input (str): User's message
        callback (function): Function to call with response
    """
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
        },
        {
            "name": "delete_event",
            "description": "delete an event on a given day",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "the title of the event the user wants to delete, which you will gather from the initial user message. Only the brief title should be included."},
                    "day": {"type": "string", "description": "the DTF of the given day without time. For example, may 24th would be 2025-05-24"}
                }
            }
        }
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {"role": "system", "content": "You are a google calendar automation assistant that will make an appropriate api call depending on the user's request. Be very concise and professional with your messages. You will be given a summary, location, description, starttime, endtime, and timezone to input in that order to a python function called 'create', which takes in all of those attributes as strings. You have access to call this function. Assume the timezone is Chicago for the last attribute after endtime, and use the dateTime format, e.g. '2025-04-30T05:00:00-05:00' for the start and end times. Return the appropriate function call with your message. You also have the ability to call the 'read10()' function that returns the user's next 10 events, make sure you call that function if you deem the user is asking for their upcoming events. Also, you have the access to the 'day_events(day)' function, where day is the user's requested day in date-time format without time included. If the user doesn't include certain unnecessary details like location or time, put None in for those arguments and proceed with creating the event. You also have the ability to call the 'delete_event(event, day)' function, where event is ONLY the title string of the event you want to delete (e.g., 'Breakfast at Kerby Lane'), and day is the user's requested day in date-time format without time included. DO NOT return the entire event object, only return the title string for the event parameter."},
            {"role": "user", "content": user_input} 
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
            },
            {
                "type": "function",
                "function": function_spec[3]
            }
        ],
        tool_choice="auto"
    )

    message = (completion.choices[0].message)

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
            callback("✅ Event created successfully")
        
        elif function_name == "read10":
            events = read10()
            callback(events)

        elif function_name == 'day_events':
            day = function_args.get('day')
            events = day_events(day=day)
            callback(events)

        elif function_name == 'delete_event':
            delete_event(title=function_args.get('title'), day=function_args.get('day'))
            callback(f"🗑️ Deleted event: {function_args.get('title')}")

    else:
        callback(message.content)

# Add PyQt6 imports for GUI
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QStatusBar
from PyQt6.QtCore import Qt, QSize

class CalendarHelperUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar Helper")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create title
        title_label = QLabel("Calendar Helper")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("font-size: 11pt; background-color: #f8f8f8; color: #333333; border-radius: 5px; padding: 10px;")
        main_layout.addWidget(self.chat_display)
        
        # Create input area
        input_layout = QHBoxLayout()
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message here...")
        self.input_box.setStyleSheet("font-size: 11pt; padding: 8px; border-radius: 5px;")
        self.input_box.setMinimumHeight(40)
        input_layout.addWidget(self.input_box)
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet("font-size: 11pt; padding: 8px; background-color: #4a86e8; color: white; border-radius: 5px;")
        send_button.setMinimumSize(QSize(80, 40))
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        main_layout.addLayout(input_layout)
        
        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to assist with your calendar")
        
        # Connect Enter key to send message
        self.input_box.returnPressed.connect(self.send_message)
        
        # Initial welcome message
        self.chat_display.append("<span style='color: #4a86e8; font-weight: bold;'>Calendar Helper:</span> Hello! I'm your calendar assistant. How can I help you today?")
        
    def send_message(self):
        """Handle sending a message"""
        user_input = self.input_box.text().strip()
        if user_input:
            # Add user message to chat display with formatting
            self.chat_display.append(f"<span style='color: #28a745; font-weight: bold;'>You:</span> {user_input}")
            
            # Disable input while processing
            self.input_box.setEnabled(False)
            self.status_bar.showMessage("Processing your request...")
            
            try:
                # Get AI response using the chat function
                self.process_ai_response(user_input)
                
                # Clear input box
                self.input_box.clear()
            except Exception as e:
                self.chat_display.append(f"<span style='color: #dc3545; font-weight: bold;'>Error:</span> {str(e)}")
                self.status_bar.showMessage(f"Error occurred: {str(e)}")
                # Re-enable input
                self.input_box.setEnabled(True)
            
    def process_ai_response(self, user_input):
        """Process the user input and get AI response"""
        def callback(response):
            # Check if the response is already HTML formatted (contains HTML tags)
            if '<' in response and '>' in response:
                # It's already HTML formatted, just add it to the chat
                self.chat_display.append(f"<div style='color: #4a86e8; font-weight: bold; margin-bottom: 8px;'>Calendar Helper:</div><div style='margin-left: 10px;'>{response}</div>")
                # Add a separator after the header if it's an event list
                if 'Your next 10 events' in response or 'Events for' in response:
                    self.chat_display.append("<div style='color: #e0e0e0; margin: 10px 0;'>________________________________________</div>")
            else:
                # Regular message formatting for non-HTML responses
                self.chat_display.append(f"<div style='color: #4a86e8; font-weight: bold; margin-bottom: 8px;'>Calendar Helper:</div><div style='margin-left: 10px;'>{response}</div>")
            
            # Update status and re-enable input
            self.status_bar.showMessage("Ready to assist with your calendar")
            self.input_box.setEnabled(True)
            self.input_box.setFocus()
        
        # Call the chat function with our input and callback
        chat(user_input, callback)
            
    @staticmethod
    def main():
        app = QApplication(sys.argv)
        window = CalendarHelperUI()
        window.show()
        sys.exit(app.exec())

if __name__ == '__main__':
    CalendarHelperUI.main()
