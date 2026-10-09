const lastCourseId = window.djangoData.lastCourseId;
const practiceId = 'b1c3b7d8-4648-4969-8604-a6161e13f5aa';

const steps = {
  '/student/': [
    {
      element: '#progressCard',
      intro: 'Here, you will be able to view upcoming assignments.'
    },
    {
      element: '#streakCard',
      intro: 'This is your streak card, and will track how many consecutive days you log into youcademy'
    }, 
    {
      element: '#reviewCard',
      intro: 'This is your review, and will tell you in how much time you need to review a particular set of flashcards.'
    }
  ],
  [`/student/course/${lastCourseId}`]: [
    {
      element: '#readingCard',
      intro: 'Here you can access your previous readings and create new ones'
    },
    {
      element: '#writingCard',
      intro: 'Here you can access your writing documents and create new ones'
    }, 
    {
      element: '#flashcardsCard',
      intro: 'Here you can open your previous flashcards and create new ones'
    }, 
    {
      element: '#readingCard',
      intro: 'This demo will cover the reading part of the platform. We will go to readings'
    }
  ], 
  [`/student/reading_menu/${lastCourseId}`]: [
    {
      element: '#datatable',
      intro: 'Here you can access your previous readings. '
    },
    {
      element: '#createNew',
      intro: 'Here you can create a new reading. Which we will do now.'
    }, 
  ], 
  [`/student/query/${lastCourseId}`]: [
    {
      element: '#topic-input',
      intro: 'Here you can enter your topic for the new reading.'
    },
    {
      element: '#submitButton',
      intro: 'Now we can submit your topic and generate the reading.'
    }, 
  ],
  [`/student/practice/${practiceId}`]: [
    {
      element: '#readingTitle',
      intro: 'Welcome to your reading. Here, you will read and ask questions to the teacher if needed.'
    },
    {
      element: '#yellowHighlight',
      intro: 'With this button you can highlight with yellow the important bits of the reading'
    }, 
    {
      element: '#pinkHighlight',
      intro: 'With this button you can highlight with pink the words or phrases that are unknown to you'
    }, 
    {
      element: '#textArea',
      intro: 'Here, you can write the notes you might need for the questions'
    }, 
    {
      element: '#teacherQuestions',
      intro: 'Here, you can ask questions to the teacher.'
    }, 
    {
      element: '#positiveFeedback',
      intro: 'And whenever possible, please help us to give feedback to this content so we can review and improve'
    }, 
    {
      element: '#negativeFeedback',
      intro: ''
    }, 
    {
      element: '#startQuestions',
      intro: 'Then, when you have finished, we can go to the questions!'
    }, 
  ],
  '/student/questions/1': [
    {
      element: '#questionBold',
      intro: 'You will have about 12 multiple choice questions, 1 highlight question and 2 open questions.'
    },
    {
      element: '#option__1',
      intro: 'Select one of the 4 answers with your mouse.'
    }, 
    {
      element: '#question_1',
      intro: 'You can click on these circles or click on the dedicated buttons to move through questions'
    }, 
  ],
  '/student/questions/15': [
    {
      element: '#submitquiz',
      intro: 'Once your are satisfied with your answers you can go ahead and submit your quiz'
    },
  ],
};

const tourOrder = [
  '/student/',
  `/student/course/${lastCourseId}`,
  `/student/reading_menu/${lastCourseId}`,
  `/student/query/${lastCourseId}`,
  `/student/practice/${practiceId}`,
  '/student/questions/1',
  '/student/questions/15'
];

function startIntro() {
  const currentPath = window.location.pathname;
  console.log("Starting intro for path:", currentPath);
  const currentSteps = steps[currentPath];
  if (currentSteps) {
    introJs().setOptions({
      steps: currentSteps,
      showProgress: true,
      showBullets: false,
      exitOnOverlayClick: false,
      exitOnEsc: false,
      nextLabel: 'Next >',
      prevLabel: '< Back',
      doneLabel: 'Finish'
    }).oncomplete(function() {
      console.log("Tour completed for path:", currentPath);
      const currentIndex = tourOrder.indexOf(currentPath);
      if (currentIndex < tourOrder.length - 1) {
        const nextPath = tourOrder[currentIndex + 1];
        console.log("Redirecting to next page:", nextPath);
        saveProgress(nextPath);
        window.location.href = nextPath;
      } else {
        const csrfToken = document.getElementById('csrf_token').value;
        console.log("Tour fully completed. Clearing progress and redirecting to /student/");
        localStorage.removeItem('introProgress');
        fetch('/api/finish-tour/', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({}),
          credentials: 'include'
      })
      .then(response => {
          // Handle the response
      })
      .catch(error => {
          // Handle the error
      });
        window.location.href = '/student/';
      }
    }).start();
  } else {
    console.log("No steps found for current path");
  }
}

function saveProgress(path) {
  console.log("Saving progress:", path);
  localStorage.setItem('introProgress', path);
}

function checkIntroProgress() {
  const savedProgress = localStorage.getItem('introProgress');
  const currentPath = window.location.pathname;
  console.log("Checking progress. Saved:", savedProgress, "Current:", currentPath);
  
  if (savedProgress) {
    if (savedProgress !== currentPath) {
      console.log("Redirecting to saved progress:", savedProgress);
      window.location.href = savedProgress;
    } else {
      console.log("Starting tour for current path");
      startIntro();
    }
  } else {
    console.log("No saved progress found");
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const currentPath = window.location.pathname;
  console.log("DOM loaded. Current path:", currentPath);
  
  if (currentPath === '/student/') {
    const tourButton = document.getElementById('beginTourBtn');
    const secondTourButton = document.getElementById('startTour');
    if (tourButton) {
      tourButton.addEventListener('click', function() {
        console.log("Begin tour button clicked");
        startIntro();
      });
    }
    if (secondTourButton) {
      secondTourButton.addEventListener('click', function() {
        console.log("Start tour button clicked");
        startIntro();
      });
    }
  } else if (tourOrder.includes(currentPath)) {
    checkIntroProgress();
  }
});

// Debugging: Log when the script loads
console.log("Multi-page tour script loaded");