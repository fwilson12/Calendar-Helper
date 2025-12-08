from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import json
from dotenv import load_dotenv
from pathlib import Path
import os

# imort stuff
from functions import create, create_recurring, readEvents, delete_event, delete_recurring, patch_event
from vars import msg_history, summary_prompt, TOOLS

# load environment variables
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

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

def chat(user_input):    
    # Add user message to history
    msg_history.append({"role": "user", "content": user_input})
    
    # Agent loop
    calling_tool = True
    called_a_tool = False
    
    while calling_tool:
        # Get agent response
        completion = client.chat.completions.create(
            model="gpt-5.1",
            messages=msg_history,
            tools=TOOLS,
            tool_choice="auto"
        )
        msg = completion.choices[0].message
        
        # Case 1: Just a text response, no tool call
        if not called_a_tool and msg.content is not None and msg.tool_calls is None:
            msg_history.append({"role": "assistant", "content": msg.content})
            return msg.content
        
        # Case 2: Previously called tool(s), now returning summary
        elif called_a_tool and msg.content is not None and msg.tool_calls is None:
            break
        
        # Case 3: Tool call
        elif msg.tool_calls is not None:
            called_a_tool = True
            tool = msg.tool_calls[0]
            msg_history.append({"role": "assistant", "tool_calls": msg.tool_calls, "content": msg.content or ""}) 
            
            # Execute tool
            function_name = tool.function.name
            function_args = json.loads(tool.function.arguments)
            result = tool_call(function_name, function_args)
            
            # add tool result to history
            msg_history.append({"role": "tool", "tool_call_id": msg.tool_calls[0].id, "content": result or ""})
    
    # get tool call(s) summary
    if called_a_tool:
        msg_history.append({"role": "system", "content": summary_prompt})
        tool_summary = client.chat.completions.create(
            model="gpt-5.1",
            messages=msg_history,
        )
        final_msg = tool_summary.choices[0].message
        msg_history.append({"role": "assistant", "content": final_msg.content})
        return final_msg.content
    
    return "uhhhh ummm"

@app.route('/')
def index():
    # Render chat interface
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat_route():
    # the yap 
    data = request.json
    user_message = data.get('message', '')
    
    # Process message and get response
    response = chat(user_message)
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)