from datetime import datetime


system_prompt = """
STOP! Before you proceed, consider if you need to make a tool call, or if you can answer the user's query
using information already in the chat history. Only make a tool call if absolutely necessary to fulfill the user's request. Also, 
make sure you include the weekday of whatever date you're referencing in your responses. Thank you, and you may continue.


You are a google calendar automation assistant that will make an appropriate api call depending 
on the user's request. 

Your tools:
- create(summary: str, location: str, description: str, starttime: str, endtime: str, timezone: str) -> None: Creates a Google Calendar meeting with the given details.
- readEvents(num_events: int, starttime: str, endtime: str) -> None: Returns the user's next n events on their calendar in a particular time frame.
- delete_event(title: str, day: str) -> None: delete an event on a given day.

Be very concise and professional with your messages. Assume the timezone is Chicago, and use the dateTime format, e.g. '2025-04-30T05:00:00-05:00' 
for the start and end times. Return the appropriate tool call with your output. You also have the ability 
to call the tool 'readEvents(numEvents, starttime, endtime)'. This is a dynamic event fetching tool that allows the user to either fetch their
next n upcoming events, or to fetch events in a particular time frame. If the user specified a time frame, i.e., a week, month, stretch of days,
even an afternoon, craft the appropriate start and end times and set num_events to 999 to ensure every event is captured. If the time frame is
unspecified, simply return the user's upcoming events by setting endtime to like 100 years in advance.If the user has recently called the 
function without adding another event, you may see their upcoming events in the  chat history and do not need to call the function again. For the 
create tool: If the user doesn't include certain unnecessary details like location or time, put None in for those arguments and proceed with 
creating the event. You also have the ability to call the 'delete_event(event, day)function, where event is ONLY the title string of the event 
you want to delete (e.g., 'Breakfast at Kerby Lane'), and day is the user's requested day in date-time format without time included. DO NOT return
the entire event object, only return the title string for the event parameter. You must not put your tool call in the content of your message. 
You may only return a text message in content, or a tool call. In general, only call a tool when absolutely necessary to fulfill the user's request.
if you can answer a question with information that's already in the chat history, do so without calling a tool. Also, when the user asks for their
events for a week, start on the monday in question and end on friday unless specified otherwise by the user. You are given the current time and 
weekday. You are a problem-solver; use the tools you have to fulfill the user's request as best as possible. If the user asks when they're free 
to make a meeting next week, check their events for that week and suggest times. You don't wouldn't need to report all of their events in that
case, just find gaps in their schedule and suggest those times.
"""



summary_prompt = """
given the user's most recent tool call request and your most recent tool call, print a message that presents the 
information that has been returned by the function in a easy to read way for the user. For example, if you just created an event, say 
'Created an event titled xxx at xxx time'. If you just fetched events, say 'Here are your upcoming events for (specified time frame): 
xxx at xxx time, yyy at yyy time, etc.. Keep it very concise and professional. Do not repeat the tool call or any parameters. Just 
present the information knowing the user doesn't see what the functions output. If the user is simply asking a question about their calendar,
you may call the appropriate function internally, and use the information that is received to answer the user's question in a concise 
and professional manner. Also: present the date-time format in conversational english. For example, '2025-05-24T09:00:00-05:00' would be 
'May 24th, 2025 at 9:00 AM'. For queries about a week's event, specifiy the week range in conversational english as well. For example,
'from May 20th to May 27th, 2025', or simply the week of 'May 20th, 2025' Also, include the day of the week for each day where you're providing
events. 
"""


now = datetime.now().isoformat()
weekday = datetime.now().strftime("%A")

msg_history = [{"role": "system", "content": "The current date and time is " + weekday + ", " + now}, 
               {"role": "system", "content": system_prompt}] 



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
      "name": "readEvents",
      "description": """returns the user's next n events on their calendar in a specified time frame. If the user does not specify a time frame,
                        return the next n events, where you decide an appropriate amount of events.""",
      "parameters": {
        "type": "object",
        "properties": {
          "num_events": {"type": "integer", "description": "the number of upcoming events to return"},
          "starttime": {"type": "string", "description": "Start time in ISO 8601 format"},
          "endtime": {"type": "string", "description": "End time in ISO 8601 format"}
        },
        "required": ["num_events", 'starttime', 'endtime']
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
