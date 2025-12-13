import { useState } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);

  const send_message = async (user_input) => {
    const response = await fetch("http://localhost:5000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: user_input }),
    });
    const data = await response.json();
    return data.response;
  };

  async function sendMessage() {
    const input = document.getElementById("userInput");
    const messagesDiv = document.getElementById("messages");
    const userInput = input.value;
    if (userInput == "") return;

    const userMsg = document.createElement("div");
    userMsg.className = "message user-message";
    userMsg.textContent = userInput;
    messagesDiv.appendChild(userMsg);
    input.value = "";

    const response = await send_message(userInput);
    const botMsg = document.createElement("div");
    botMsg.className = "message bot-message";
    botMsg.textContent = response;
    messagesDiv.appendChild(botMsg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  return (
    <>
      <h1>Calendar Helper</h1>
      <div className="chat-container">
        <div className="messages" id="messages"></div>
        <div className="input-area">
          <input
            type="text"
            id="userInput"
            placeholder="Type your message..."
          />
          <button onClick={() => sendMessage()}>Send</button>
        </div>
      </div>
    </>
  );
}

export default App;
