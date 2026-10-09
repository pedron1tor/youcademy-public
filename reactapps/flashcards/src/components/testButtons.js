import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
export const TestModeButtons = ({ currentCardFlipRef, cards, currentCardIndex, setCurrentCardIndex, controlRef, url, qid, setCards, setIsFinished }) => {
  const [isAnswerVisible, setIsAnswerVisible] = useState(false);
  const [showAgainCards, setShowAgainCards] = useState([]);

  const toggleAnswer = () => {
    currentCardFlipRef.current();
    setIsAnswerVisible(!isAnswerVisible);
  };

  const sendResponse = async (cards, currentCardIndex, difficulty) => {
    const csrfToken = getCsrfToken();
    const currentCard = cards[currentCardIndex];
    console.log("Current card", currentCardIndex);
    try {
      const response = await axios.post(`${url}/api/card-response/`, { currentCard, difficulty, qid }, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      });
      
      console.log("Cards saved successfully");
      console.log(response.data.show_again);
      
      if (response.data.show_again) {
        return new Promise(resolve => {
          setShowAgainCards(prevCards => {
            const cardExists = prevCards.some(card => card.id === currentCard.id);
            if (!cardExists) {
              const newCards = [...prevCards, currentCard];
              resolve(newCards);
              return newCards;
            }
            resolve(prevCards);
            return prevCards;
          });
        });
      }
      return Promise.resolve(showAgainCards);
    } catch (error) {
      console.error("Failed to save cards", error);
      throw error;
    }
  };

  const modifyDeckAndRestart = async (updatedShowAgainCards) => {
    if (updatedShowAgainCards.length > 0)
    {console.log("These are the showagain cards", updatedShowAgainCards);
    setCards(updatedShowAgainCards);
    setCurrentCardIndex(0);
    controlRef.current.resetArray(updatedShowAgainCards);
    setShowAgainCards([]);}
    else {
      console.log("you have finished reviewing");
      setIsFinished(true);
      const csrfToken = getCsrfToken();
      axios.post(`${url}/api/due-dates-mdb-sql/`, { qid, }, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      });
    }
  };

  const handleDifficulty = async (difficulty) => {
    try {
      if (difficulty === 'again') {
        currentCardFlipRef.current();
        await sendResponse(cards, currentCardIndex, difficulty);
      } else {
        const updatedShowAgainCards = await sendResponse(cards, currentCardIndex, difficulty);
        
        const nextIndex = (currentCardIndex + 1) % cards.length;
        
        if (nextIndex === 0) {
          currentCardFlipRef.current();
          await modifyDeckAndRestart(updatedShowAgainCards);
        } else {
          currentCardFlipRef.current();
          controlRef.current.nextCard();
          setCurrentCardIndex(nextIndex);
        }
      }
      
      setIsAnswerVisible(false);
    } catch (error) {
      console.error("Error handling difficulty:", error);
      // Handle the error appropriately
    }
  };

  return (
    <div className="mt-2 pointer-events-auto flex flex-col items-center" style={{ width: "400px" }}>
      <button 
        className={`
          bg-[#265a82]  
          hover:bg-[#1d4361] 
          text-white 
          px-4 
          rounded 
          mb-4
          flex 
          items-center 
          justify-center
          h-10
          transition duration-300 ease-in-out
          w-full
        `}
        onClick={toggleAnswer}
      >
        {isAnswerVisible ? "Hide Answer" : "Show Answer"}
      </button>
      
      {isAnswerVisible && (
        <div className="flex justify-between w-full">
          <button onClick={() => handleDifficulty('again')} className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Again</button>
          <button onClick={() => handleDifficulty('hard')} className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Hard</button>
          <button onClick={() => handleDifficulty('good')} className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Good</button>
          <button onClick={() => handleDifficulty('easy')} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Easy</button>
        </div>
      )}
    </div>
  );
};

export function TestModeButton({ startTestMode, exitTestMode, isTestMode }) {
  return (
    <button
      className={`
        bg-${isTestMode ? "red" : "green"}-500 
        hover:bg-${isTestMode ? "red" : "green"}-700 
        text-white 
        px-4 
        rounded 
        mb-4
        flex 
        items-center 
        justify-center
        h-10
        transition duration-300 ease-in-out
      `}
      onClick={isTestMode ? exitTestMode : startTestMode}
    >
      {isTestMode ? "Exit Test Mode" : "Start Test Mode"}
    </button>
  );
}
export const getCsrfToken = () => {
  const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
  return csrfMetaTag ? csrfMetaTag.getAttribute('content') : '';
};