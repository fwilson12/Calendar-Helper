from openai import OpenAI
import json

from dotenv import load_dotenv
from pathlib import Path
import os

from functions import create, create_recurring, readEvents, delete_event, delete_recurring, patch_event

SCOPES = ["https://www.googleapis.com/auth/calendar"]



env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)


from vars import msg_history, summary_prompt, TOOLS



def tool_call(function_name, function_args):
  if function_name == "create":
    return create(
      summary=function_args.get('summary', ''),
      location=function_args.get('location', ''),
      description=function_args.get('description', ''),
      starttime=function_args.get('starttime'),
      endtime=function_args.get('endtime'),
      timezone=function_args.get('timezone')
          )
    
  elif function_name == "create_recurring":
    return create_recurring(
      summary=function_args.get('summary', ''),
      location=function_args.get('location', ''),
      description=function_args.get('description', ''),
      starttime=function_args.get('starttime'),
      endtime=function_args.get('endtime'),
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


while True:

  user_input = input("\nUser: ")
  if user_input == "exit":
    break
  msg_history.append({"role": "user", "content": user_input})
  completion = client.chat.completions.create(
    model="gpt-5.1",
    messages=msg_history,
    tools=TOOLS,
    tool_choice="auto"
  )
  msg = completion.choices[0].message
  
  if msg.content is not None and msg.tool_calls is None:
    print("Assistant: " + msg.content)
    msg_history.append({"role": "assistant", "content": msg.content})
      
  if msg.tool_calls is not None:
    tool = msg.tool_calls[0]
    msg_history.append({"role": "assistant", "tool_calls": msg.tool_calls, "content": msg.content or ""})
    
    function_name = tool.function.name
    function_args = json.loads(tool.function.arguments)

    result = tool_call(function_name, function_args)

    msg_history.append({"role": "tool", "tool_call_id": msg.tool_calls[0].id, "content": result or ""})
    
    msg_history.append({"role": "system", "content": summary_prompt})
    completion2 = client.chat.completions.create(
        model="gpt-5.1",
        messages=msg_history,
        tools=TOOLS,
        tool_choice="auto"
    )
    msg2 = completion2.choices[0].message
    
    
    if msg2.content is not None and msg2.tool_calls is None:
      print("Assistant: " + msg2.content)
      msg_history.append({"role": "assistant", "content": msg2.content})
        
    if msg2.tool_calls is not None:
      tool = msg2.tool_calls[0]
      msg_history.append({"role": "assistant", "tool_calls": msg2.tool_calls, "content": msg2.content or ""})
      
      function_name = tool.function.name
      function_args = json.loads(tool.function.arguments)

      result = tool_call(function_name, function_args)

      msg_history.append({"role": "tool", "tool_call_id": msg2.tool_calls[0].id, "content": result or ""})
      
      msg_history.append({"role": "system", "content": summary_prompt})

      completionFinal = client.chat.completions.create(
          model="gpt-5.1",
          messages=msg_history,
      )
      msgFinal = completionFinal.choices[0].message

      print("Assistant: " + msgFinal.content)
      msg_history.append({"role": "assistant", "content": msgFinal.content})


  print(msg_history)

