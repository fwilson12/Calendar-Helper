from openai import OpenAI
import json

from dotenv import load_dotenv
from pathlib import Path
import os
from functions import create, readEvents, delete_event

SCOPES = ["https://www.googleapis.com/auth/calendar"]



env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)


from vars import msg_history, function_spec, summary_prompt, now, weekday

#print("The current time is " + weekday + ", " + now)

while True:

  user_input = input("User: ")
  if user_input == "exit":
    break
  msg_history.append({"role": "user", "content": user_input})
  completion = client.chat.completions.create(
    model="gpt-5.1",
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
    }
    ],
    tool_choice="auto"
  )


  #print(completion.choices[0].message)
  msg = completion.choices[0].message
  
  if msg.content is not None:
    print("Assistant: " + completion.choices[0].message.content)
    msg_history.append({"role": "assistant", "content": msg.content})
      
  if msg.tool_calls is not None:
    tool_call = msg.tool_calls[0]
    
    # print(msg.tool_calls[0])
    
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
      
    elif function_name == "readEvents":
      readEvents(
        num_events=function_args.get('num_events'),
        startime=function_args.get('starttime'),
        endtime=function_args.get('endtime')
        )

    elif function_name == 'delete_event':
      delete_event(title=function_args.get('title'), day=function_args.get('day'))
      


    msg_history.append({"role": "assistant", "content": "Called tool: " + tool_call.function.name + " with arguments " + str(tool_call.function.arguments)})
    
    msg_history.append({"role": "user", "content": summary_prompt}) 
    completion2 = client.chat.completions.create(
        model="gpt-5.1",
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
        }
        ],
        tool_choice="auto"
    )
    msg2 = completion2.choices[0].message
    print("Assistant: " + msg2.content)
    msg_history.append({"role": "assistant", "content": msg2.content})

