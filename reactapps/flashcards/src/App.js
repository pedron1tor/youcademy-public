import React, { useState, useEffect, useRef } from "react";
import { FlashcardArray } from "react-quizlet-flashcard";
import axios from "axios";
import "./App.css";
import {TestModeButton, TestModeButtons, getCsrfToken} from "./components/testButtons.js";

function App() {
  const [cards, setCards] = useState([]);
  const [isEditMode, setIsEditMode] = useState(true);
  const [isTestMode, setIsTestMode] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [userInput, setUserInput] = useState("");
  const [tries, setTries] = useState(0);
  const [hint, setHint] = useState("");
  const [message, setMessage] = useState("");
  const [freeze, setFreeze] = useState(true);
  const [learningCount, setLearningCount] = useState(0);
  const [cardsBeforeTestMode, setCardsBeforeTestMode] = useState(0);
  const controlRef = useRef({});
  const appElement = document.getElementById("react-app");
  const [audioPaths, setAudioPaths] = useState([]);
  const audioRef = useRef(new Audio());
  const currentCardFlipRef = useRef();
  const [isFinished, setIsFinished] = useState(false);
  let params = {};
  if (appElement) {
    const userId = appElement.getAttribute("data-user-id");
    const qid = appElement.getAttribute("data-qid");
    params = { qid, userId };
  }
  const handleImageUpload = async (cardId, side, event) => {
    const file = event.target.files?.[0];
    if (file) {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('cardId', cardId.toString());
      formData.append('side', side);
      formData.append('qid', params.qid);
      formData.append('userId', params.userId);
  
      try {
        const response = await axios.post(`${url}/api/upload-flashcard-image/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': getCsrfToken(), 
          },
        });
  
        if (response.data && response.data.imageUrl) {

        }
      } catch (error) {
        console.error('Error uploading image:', error);
      }
    }
  };
  const url = appElement ? appElement.getAttribute('data-url') || '' : '';

  useEffect(() => {
    axios
      .get(`${url}/api/get-flashcards/`, { params })
      .then((response) => {
        setCards(response.data.cards);
        console.log(response.data.cards);
        setLearningCount(response.data.cards.length);
      })
      .catch((error) => {
        console.error("Failed to fetch initial data for the editor", error);
      });
  }, []);
  
  useEffect(() => {
    setFreeze(true);
  }, [currentCardIndex]);

  const handleInputChange = (id, side, value) => {
    console.log(value);
    setCards(
      cards.map((card) => (card.id === id ? { ...card, [side]: value } : card))
    );
    console.log(cards);
  };

  const shuffleCards = () => {
    const shuffledCards = [...cards].sort(() => Math.random() - 0.5);
    setCards(shuffledCards);
  };

  useEffect(() => {
    if (cards.length > 0 && !isTestMode) {
      const newurl = `${url}/api/save-flashcards/?${new URLSearchParams(params).toString()}`;
      const csrfToken = getCsrfToken();
      axios.post(newurl, { cards }, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      })
      .then((response) => {
        console.log("Cards saved successfully");
      })
      .catch((error) => {
        console.error("Failed to save cards", error);
      });
    }
  }, [cards]);

  const startTestMode = () => {
    shuffleCards();
    setCurrentCardIndex(0);
    setIsTestMode(true);
    setUserInput("");
    setTries(0);
    setCardsBeforeTestMode(cards);
    setHint("");
    setMessage("");
    setIsFinished(false);
    setFreeze(true);
    controlRef.current.resetArray();
  };

  const playAudio = (index, frontHTML) => {
    console.log(index);
    console.log("Playing audio: ", audioPaths);
    console.log("Playing audio: ", audioPaths[index]);
    if (audioPaths[index]) {
      console.log("Playing audio: ", audioPaths[index][frontHTML]);
      audioRef.current.src = audioPaths[index][frontHTML];
      audioRef.current.play();
    }
  };

  const exitTestMode = () => {
    setCards(cardsBeforeTestMode);
    setIsTestMode(false);
    setIsFinished(false);
  };

  const addCard = () => {
    const newCard = { id: Date.now(), frontHTML: "", backHTML: "" };
    setCards([newCard, ...cards]);
    console.log(cards);
  };

  const removeCard = (id) => {
    setCards(cards.filter((card) => card.id !== id));
  };

  const handleViewCards = () => {
    console.log(document.getElementById("root"));
    if (document.getElementById("root")) {
      document.getElementById("root").style.overflowY = "hidden";
    }

    const newurl = `${url}/api/save-flashcards/?${new URLSearchParams(
      params
    ).toString()}`;
    const csrfToken = getCsrfToken();
    axios
      .post(newurl, { cards },{
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      })
      .then((response) => {
        console.log("Cards saved successfully");
        setIsEditMode(false);
      })
      .catch((error) => {
        console.error("Failed to save cards", error);
      });
      setIsEditMode(false);
      const csrfToken2 = getCsrfToken();  
    axios
      .post(`${url}/api/get-tts/`, { cards, params }, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken2,
        },})
        .then((response) => {
          console.log("TTS request sent successfully");
          setAudioPaths(response.data.file_paths);
        });
  };

  const handleCardChange = (cardData, cardIndex) => {
    setCurrentCardIndex(cardIndex-1);
  };

  const resetCardIndex = () => {
    setCurrentCardIndex(0);
  }

  return (
    <>
      <div
        className={`bg-white dark:bg-gray-800 min-h-screen text-black dark:text-white ${
          !isEditMode && "overflow-hidden"
        }`}
        style={{
          scrollbarColor: "darkblue transparent",
          scrollbarWidth: "thin",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {isTestMode && isFinished ? (
          <div className="fixed inset-0 bg-white dark:bg-gray-800 z-50 flex flex-col items-center justify-center p-4">
            <h2 className="text-2xl font-bold mb-4 text-center">
              Congratulations! You have finished this deck for now.
            </h2>
            <p className="text-lg mb-8 text-center">
              If you wish to study outside of the regular schedule, you can use the custom study feature.
            </p>
            <button
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              onClick={exitTestMode}
            >
              Exit Test Mode
            </button>
          </div>
        ) : (
          <>
            <div className="flex align-middle justify-center items-center">
              {isEditMode ? (
                <div
                  className="flex align-middle justify-between mb-4"
                  style={{ minWidth: "400px" }}
                >
                  {cards.length > 0 && (
                    <button
                      className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-700"
                      onClick={handleViewCards}
                    >
                      View Cards
                    </button>
                  )}
                  <button
                    className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-700"
                    onClick={addCard}
                  >
                    Add Card
                  </button>
                </div>
              ) : (
                <>
                  {!isTestMode && (
                    <div className="flex justify-between items-center w-1/2">
                      <button
                        className="bg-yellow-500 text-white py-2 px-4 rounded hover:bg-yellow-700"
                        onClick={() => {
                          setIsEditMode(true);
                          resetCardIndex();
                          if (document.getElementById("root")) {
                            document.getElementById("root").style.overflowY = "auto";
                          }
                        }}
                      >
                        Edit Cards
                      </button>
                      {!isTestMode && (
                        <button 
                          className="p-2 ml-4"
                          onClick={() => playAudio(currentCardIndex, cards[currentCardIndex].frontHTML)}
                        >
                          <img 
                            src="https://upload.wikimedia.org/wikipedia/commons/2/21/Speaker_Icon.svg" 
                            alt="Speaker icon"
                            className="w-5 h-5"
                          />
                        </button>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
  
            {isEditMode ? (
              <div className="flex flex-col align-middle justify-center items-center">
                {cards.map((card) => (
                  <div
                  key={card.id}
                  className="mb-3 p-4 border rounded shadow bg-gray-100 dark:bg-gray-700 flex flex-col align-middle justify-center"
                  style={{ minWidth: "600px" }}
                >
                  <div className="relative mb-2">
                    
                    <div className="flex justify-center mb-2">
                      <img 
                        src=""  
                        className="w-1/4 h-auto mb-2"
                      />
                    </div>

                    <div className="relative">
                      <input
                        className="border p-2 w-full rounded bg-white dark:bg-gray-800 text-black dark:text-white pr-10"
                        type="text"
                        value={card.frontHTML}
                        onChange={(e) =>
                          handleInputChange(card.id, "frontHTML", e.target.value)
                        }
                        placeholder="Front"
                      />
                      <label htmlFor={`frontUpload-${card.id}`} className="absolute right-2 top-1/2 transform -translate-y-1/2 cursor-pointer">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                      </label>
                      <input
                        id={`frontUpload-${card.id}`}
                        type="file"
                        className="hidden"
                        onChange={(e) => handleImageUpload(card.id, "frontHTML", e)}
                        accept="image/*"
                      />
                    </div>
                  </div>
                  <div className="relative mb-2">
                  <div className="flex justify-center mb-2">
                      <img 
                        src="" 
                        className="w-1/4 h-auto mb-2"
                      />
                    </div>
                    <div className="relative">
                    <input
                      className="border p-2 w-full rounded bg-white dark:bg-gray-800 text-black dark:text-white pr-10"
                      type="text"
                      value={card.backHTML}
                      onChange={(e) =>
                        handleInputChange(card.id, "backHTML", e.target.value)
                      }
                      placeholder="Back"
                    />
                    <label htmlFor={`backUpload-${card.id}`} className="absolute right-2 top-1/2 transform -translate-y-1/2 cursor-pointer">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                    </label>
                    <input
                      id={`backUpload-${card.id}`}
                      type="file"
                      className="hidden"
                      onChange={(e) => handleImageUpload(card.id, "backHTML", e)}
                      accept="image/*"
                    />
                    </div>
                  </div>
                  <button
                    className="bg-red-500 text-white py-2 px-4 rounded hover:bg-red-700"
                    onClick={() => removeCard(card.id)}
                  >
                    Remove Card
                  </button>
                </div>
                ))}
              </div>
            ) : (
              <div
                className={`mt-2`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexDirection: "column",
                  pointerEvents: isTestMode ? "none" : "auto",
                }}
              >
                <FlashcardArray
                  cards={cards}
                  startIndex={currentCardIndex}
                  FlashcardArrayStyle={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    marginTop: "20px",
                  }}
                  frontCardStyle={{
                    justifyContent: "center",
                    alignItems: "center",
                  }}
                  frontContentStyle={{
                    backgroundColor: "#f8f8f8",
                    border: "2px solid #ddd",
                    borderRadius: "10px",
                    padding: "20px",
                    textAlign: "center",
                    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
                    fontSize: "3rem",
                    justifyContent: "center",
                    alignItems: "center",
                    display: "flex",
                  }}
                  backContentStyle={{
                    backgroundColor: "#e0e0e0",
                    border: "2px solid #ccc",
                    borderRadius: "10px",
                    padding: "20px",
                    textAlign: "center",
                    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
                    fontSize: "1.6rem",
                    justifyContent: "center",
                    alignItems: "center",
                    display: "flex",
                  }}
                  forwardRef={controlRef}
                  controls={!isTestMode}
                  style={{ pointerEvents: isTestMode ? "none" : "auto" }}
                  onCardChange={handleCardChange}
                  {...(isTestMode && { currentCardFlipRef: currentCardFlipRef })}
                />
                <div className="mt-4">
                  {!isTestMode && (
                    <TestModeButton
                      startTestMode={startTestMode}
                      exitTestMode={exitTestMode}
                      isTestMode={isTestMode}
                    />
                  )}
                </div>
              </div>
            )}
  
            {isTestMode && (
              <div
                className="mt-2 pointer-events-auto flex flex-col"
                style={{
                  width: "400px",
                  alignItems: "center",
                  alignSelf: "center",
                }}
              >
                <TestModeButtons 
                  currentCardFlipRef={currentCardFlipRef} 
                  cards={cards} 
                  currentCardIndex={currentCardIndex} 
                  setCurrentCardIndex={setCurrentCardIndex} 
                  controlRef={controlRef} 
                  url={url} 
                  qid={params.qid} 
                  setCards={setCards}
                  setIsFinished={setIsFinished}
                />          
                <div className="absolute -bottom-2 right-3">
                  <TestModeButton
                    startTestMode={startTestMode}
                    exitTestMode={exitTestMode}
                    isTestMode={isTestMode}
                  />
                </div>
              </div>
            )}
  
            {message && (
              <div className="mb-4 text-lg font-bold text-center">{message}</div>
            )}
          </>
        )}
      </div>
    </>
  );
}

export default App;
