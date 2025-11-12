from openai import OpenAI
import json

from dotenv import load_dotenv
from pathlib import Path
import os
from functions import create, read10, day_events, delete_event

SCOPES = ["https://www.googleapis.com/auth/calendar"]



env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)


from vars import msg_history
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

while True:

  user_input = input("User: ")
  msg_history.append({"role": "user", "content": user_input})
  completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=msg_history,
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


  #print(completion.choices[0].message)
  msg = completion.choices[0].message
  
  if msg.content is not None:
    print("Assistant: " + completion.choices[0].message.content)
    msg_history.append({"role": "assistant", "content": msg.content})
      
  elif msg.tool_calls is not None:
    tool_call = msg.tool_calls[0]
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

    elif function_name == 'delete_event':
      delete_event(title=function_args.get('title'), day=function_args.get('day'))

      


    msg_history.append({"role": "assistant", "content": "Called tool: " + tool_call.function.name + " with arguments " + str(tool_call.function.arguments)})
    
    msg_history.append({"role": "user", "content": "in a few words generally describe the action you just performed in plain language, as if you're presenting the results/call you made (e.g. created an event at xxx at xxx time, or here's your upcoming events)"}) 
    completion2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=msg_history,
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
    msg2 = completion2.choices[0].message
    print("Assistant: " + msg2.content)
    msg_history.append({"role": "assistant", "content": msg2.content})

