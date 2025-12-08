from openai import OpenAI
import json

from dotenv import load_dotenv
from pathlib import Path
import os

# get tools for agent
from functions import create, create_recurring, readEvents, delete_event, delete_recurring, patch_event

# for google api calls
SCOPES = ["https://www.googleapis.com/auth/calendar"]


# for openai api key
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)


# agent context stuff 
from vars import msg_history, summary_prompt, TOOLS


# handles whatever tool call the guy makes
def tool_call(function_name, function_args):
  if function_name == "create":
    return create(
      summary=function_args.get('summary', ''),
      location=function_args.get('location', ''),
      description=function_args.get('description', ''),
      start=function_args.get('start'),
      end=function_args.get('end'),
      timezone=function_args.get('timezone')
          )
    
  elif function_name == "create_recurring":
    return create_recurring(
      summary=function_args.get('summary', ''),
      location=function_args.get('location', ''),
      description=function_args.get('description', ''),
      start=function_args.get('start'),
      end=function_args.get('end'),
      timezone=function_args.get('timezone'),
      frequency=function_args.get('frequency'), 
      interval=function_args.get('interval'),
      weekdays=function_args.get('weekdays'),
      monthday=function_args.get('monthday'),
      nth_weekday=function_args.get('nth_weekday'),
      until=function_args.get('until'),
      count=function_args.get('count'),
      exception_dates=function_args.get('exception_dates')

    )
  
  elif function_name == "readEvents":
    return readEvents(
      num_events=function_args.get('num_events'),
      starttime=function_args.get('starttime'),
      endtime=function_args.get('endtime')
      )

  elif function_name == 'delete_event':
    return delete_event(
      title=function_args.get('title'), 
      starttime=function_args.get('starttime'),
      endtime=function_args.get('endtime')
      )
  
  elif function_name == 'delete_recurring':
    return delete_recurring(
      title=function_args.get('title'), 
      starttime=function_args.get('starttime'),
      endtime=function_args.get('endtime')
      )
    
  elif function_name == 'patch_event':
    return patch_event(
      title=function_args.get('title'),
      starttime=function_args.get('starttime'),
      endtime=function_args.get('endtime'),
      patch_body=function_args.get('patch_body'),
      modify_series=function_args.get('modify_series', False)
      )

# handles agent response loop, if a tool was previously called, summarize it. defaults to false (if the previous agent action was just a message)
def chat(prev_tool_call = False):
  
  # if a tool was called in the last iteration, summarize it
  if prev_tool_call:
    msg_history.append({"role": "system", "content": summary_prompt})
    tool_summary = client.chat.completions.create(
            model="gpt-5.1",
            messages=msg_history,
        )
    msgFinal = tool_summary.choices[0].message

    print("Assistant: " + msgFinal.content)
    msg_history.append({"role": "assistant", "content": msgFinal.content})
    for msg in msg_history:
      print(msg) # debugging 
  
  # gather new user input
  user_input = input("\nUser: ")
  if user_input == "exit":
    return
  msg_history.append({"role": "user", "content": user_input})
 
  # initialize loop 
  calling_tool = True
  called_a_tool = False
  while calling_tool:
    
    # agent response 
    completion = client.chat.completions.create(
      model="gpt-5.1",
      messages=msg_history,
      tools=TOOLS,
      tool_choice="auto"
    )
    msg = completion.choices[0].message
    
    # if the dude only is saying something (w/o previously calling a tool), exit loop and move on to user response in recursive call
    if not called_a_tool and msg.content is not None and msg.tool_calls is None:
      print("Assistant: " + msg.content)
      msg_history.append({"role": "assistant", "content": msg.content})
      # break from loop
      calling_tool = False
      
      for msg in msg_history:
        print(msg) # debugging 

    # if the bot called a tool in its last message but not its current message, proceed to recursive call where its actions will be summarized
    elif called_a_tool and msg.content is not None and msg.tool_calls is None:
      break

    # if the guy calls a tool, continue the loop
    elif msg.tool_calls is not None:
      called_a_tool = True
      tool = msg.tool_calls[0]
      msg_history.append({"role": "assistant", "tool_calls": msg.tool_calls, "content": msg.content or ""})
      
      # load the function/arguments from the tool call our guy returned 
      function_name = tool.function.name
      function_args = json.loads(tool.function.arguments)
      
      # the text that our tool functions return
      result = tool_call(function_name, function_args)

      # add the tool call to message history, the call_id field is required, adds content if there is any 
      msg_history.append({"role": "tool", "tool_call_id": msg.tool_calls[0].id, "content": result or ""})
  
  # call recursively with info about agent's last action (response or tool call)
  chat(called_a_tool)

chat()