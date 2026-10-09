import { useState, useEffect, useRef } from "react";
import { useChat } from "ai/react"; // Ensure this module exists or is correctly implemented
import clsx from "clsx";
import { LoadingCircle, SendIcon } from "./icons/icons";
import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Textarea from "react-textarea-autosize";
import axios from 'axios';

type Message = {
  content: string;
  role: 'user' | 'system';
};

const examples = [
  "Please respond to my queries in Dutch",
  "Please respond to my queries in English",
  "Suggest a topic to write an article about",
];

const HEARTBEAT_INTERVAL = 5 * 60 * 1000; // Heartbeat interval in milliseconds (5 minutes)

export default function Chat() {
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const websocket = useRef<WebSocket | null>(null);
  const heartbeatInterval = useRef<number | null>(null);
  const reconnectTimeout = useRef<number | null>(null);

  const setupWebSocket = () => {
    const appElement = document.getElementById('react-app2');
    let wsUrl = 'ws://127.0.0.1:8000/ws/chat/';
    let prompt = '';

    if (appElement) {
      wsUrl = appElement.getAttribute('data-wsurl') || '';
      prompt = appElement.getAttribute('data-prompt') || '';
    }

    websocket.current = new WebSocket(wsUrl);

    websocket.current.onopen = () => {
      console.log("WebSocket connected at " + wsUrl);
      websocket.current?.send(JSON.stringify({
        type: 'initialize',
        prompt: prompt
      }));

      // Set up heartbeat interval
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }
      heartbeatInterval.current = window.setInterval(() => {
        if (websocket.current?.readyState === WebSocket.OPEN) {
          console.log('Sending heartbeat');
          websocket.current.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, HEARTBEAT_INTERVAL); 
    };

    websocket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.message) {
        console.log('Received:', data.message);
        setMessages(messages => [...messages, { content: data.message, role: 'system' }]);
      } else if (data.type === 'heartbeat_ack') {
        console.log('Received heartbeat acknowledgment');
      }
    };

    websocket.current.onclose = () => {
      console.log("WebSocket disconnected");
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      reconnectTimeout.current = window.setTimeout(setupWebSocket, 5000); // Try to reconnect every 5 seconds
    };

    websocket.current.onerror = (error) => {
      console.error("WebSocket error", error);
      websocket.current?.close();
    };
  };

  useEffect(() => {
    setupWebSocket();

    return () => {
      if (websocket.current) {
        websocket.current.close();
      }
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, []);

  useEffect(() => {
    const appElement = document.getElementById('react-app2');
    let params = {};
    let url = '';

    if (appElement) {
      const userId = appElement.getAttribute('data-user-id') || '';
      const qid = appElement.getAttribute('data-qid') || '';
      params = { qid, userId };
      url = appElement.getAttribute('data-url') || '';
    }

    if (url) {
      axios.get(`${url}/api/get-chat-session/`, { 
        params,
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(response => {
          console.log('Messages fetched:', response.data.messages);
          setMessages(response.data.messages);
        })
        .catch(error => {
          console.error('Failed to fetch initial data for the editor', error);
        });
    }
  }, []);

  const { isLoading } = useChat({
    onResponse: (response) => {
      if (response.status === 429) {
        console.error("You have reached your request limit for the day.");
        return;
      }
    },
    onError: (error) => {
      console.error("Chat error:", error.message);
    },
  });

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!input.trim()) {
      console.log("Input is empty!");
      return;
    }
    
    const appElement = document.getElementById('react-app2');
    let userId = '';
    let qid = '';
    let occupation = '';
    
    if (appElement) {
      userId = appElement.getAttribute('data-user-id') || ''; 
      qid = appElement.getAttribute('data-qid') || ''; 
      occupation = appElement.getAttribute('data-occupation') || ''; 
    }

    if (websocket.current) {
      websocket.current.send(JSON.stringify({ message: input, userId, qid, occupation }));
      setMessages(messages => [...messages, { content: input, role: 'user' }]);
    }
  
    setInput("");
  };

  const disabled = isLoading || input.length === 0;
  const [scrollingUp, setScrollingUp] = useState(false);
  const messagesEndRef = useRef(null);
  const prevScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY < prevScrollY.current) {
        setScrollingUp(true);
      } else {
        setScrollingUp(false);
      }
      prevScrollY.current = window.scrollY;
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    if (!scrollingUp) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, scrollingUp]);

  return (
    <main className="flex flex-col items-center justify-start pb-30 h-full" style={{ height: '700px', position: 'relative' }}>
      <div className={`flex flex-col w-full items-center justify-start pb-40 ${messages.length > 0 ? 'overflow-auto' : ''}`} style={{ flexGrow: 1 }}>
        {messages.length > 0 ? (
          messages.map((message, i) => (
            <div
              key={i}
              className={clsx(
                "flex w-full items-center justify-center border-b border-gray-200 py-4",
                message.role === "user" ? "bg-white" : "bg-gray-100",
              )}
            >
              <div className="flex w-full max-w-screen-md items-start space-x-4 px-5 sm:px-0">
                <div
                  className={clsx(
                    "p-1.5 text-white rounded-full",
                    message.role === "system" ? "bg-green-500" : "bg-black",
                  )}
                >
                  {message.role === "user" ? <User width={20} /> : <Bot width={20} />}
                </div>
                <ReactMarkdown
                  className="prose mt-1 w-full break-words prose-p:leading-relaxed"
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ node, ...props }) => (
                      <a {...props} target="_blank" rel="noopener noreferrer" />
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          ))
        ) : (
          <div className="border-gray-200 sm:mx-0 mx-5 mt-0 max-w-screen-md rounded-md border sm:w-full">
            <div className="flex flex-col space-y-4 p-7 sm:p-10">
              <h1 className="text-lg font-semibold text-black">
                Welcome to Youcademy Writing!
              </h1>
            </div>
            <div className="flex flex-col space-y-4 border-t border-gray-200 bg-gray-50 p-7 sm:p-10">
              {examples.map((example, i) => (
                <button
                  key={i}
                  className="rounded-md border border-gray-200 bg-white px-5 py-3 text-left text-sm text-gray-500 transition-all duration-75 hover:border-black hover:text-gray-700 active:bg-gray-50"
                  onClick={() => {
                    setInput(example);
                    inputRef.current?.focus();
                  }}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="flex w-full flex-col items-center space-y-3 p-5 pb-3 sm:px-0" style={{ position: 'absolute', bottom: 0, left: 0, width: '100%' }}>
        <form
          ref={formRef}
          onSubmit={handleSubmit}
          className={clsx(
            "relative w-full max-w-screen-md rounded-xl border border-gray-200 bg-white px-4 pb-2 pt-3 shadow-sm sm:pb-3 sm:pt-4",
            scrollingUp ? 'sticky' : 'bottom-0'
          )}
        >
          <Textarea
            ref={inputRef}
            tabIndex={0}
            required
            rows={1}
            autoFocus
            placeholder="Send a message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                formRef.current?.requestSubmit();
                e.preventDefault();
              }
            }}
            spellCheck={false}
            className="w-full pr-10 focus:outline-none"
          />
          <button
            className={clsx(
              "absolute inset-y-0 right-3 my-auto flex h-8 w-8 items-center justify-center rounded-md transition-all",
              disabled ? "cursor-not-allowed bg-white" : "bg-green-500 hover:bg-green-600",
            )}
            disabled={disabled}
          >
            {isLoading ? <LoadingCircle /> : <SendIcon className="text-white h-4 w-4" />}
          </button>
        </form>
      </div>
    </main>
  );
}
