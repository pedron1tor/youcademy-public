import textwrap
files = [
    ("10L.pdf", 10),
    ("40L .pdf", 40),
    ("40 L.pdf", 40),
    ("70L.pdf", 70),
    ("90L .pdf", 90),
    ("100 L.pdf", 100),
    ("120 L .pdf", 120),
    ("140L.pdf", 140),
    ("240 L .pdf", 240),
    ("290 L.pdf", 290),
    ("350 L .pdf", 350),
    ("380 L.pdf", 380),
    ("400 L.pdf", 400),
    ("440 L.pdf", 440),
    ("460 L.pdf", 460),
    ("500L.pdf", 500),
    ("570 L.pdf", 570),
    ("690 L.pdf", 690),
    ("720 L.pdf", 720),
    ("730.pdf", 730),
    ("740 L.pdf", 740),
    ("810 L.pdf", 810),
    ("840 L.pdf", 840),
    ("910 L .pdf", 910),
    ("970L.pdf", 970),
    ("990 L.pdf", 990),
    ("1040 L.pdf", 1040),
    ("1070 L.pdf", 1070),
    ("1110 L .pdf", 1110),
    ("1150 L .pdf", 1150),
    ("1190 L.pdf", 1190),
    ("1200 L .pdf", 1200),
    ("1220 L.pdf", 1220),
    ("1250L.pdf", 1250),
    ("1350 L.pdf", 1350),
    ("1360 L .pdf", 1360),
]
metrics_for_writing = {
        "descriptive":
        """A thing that the readers will be assessed to identify and describe the descriptive features in the text. A text that is organized with a descriptive or informational text structure organizes information by describing the attributes and details of a person, place, thing, idea, or event. The author presents a main idea, divides the text into related subtopics, and then supports the text with informational details. Descriptive text might use sensory details because they allow readers to visualize as they read.

  The text you are going to write should lend itself to answer questions like:  Why did the author use this text structure? What can you learn from this structure? And focus on words that are typical for this type of text: for example, such as, most importantly, specifically, in addition, for instance, to illustrate, described as, another, is like, and including. Include some of these words in the text you will generate. Make it clearly descriptive. 
  """,
        "genre":
        """A thing that the readers will be assessed on is their ability to identify and describe the characteristics of the genre. The term genre is also known as the type of text and is often categorized as fiction or nonfiction. Fiction texts are often presented in the form of stories with characters and a plot. Fiction can also be narrowed down into text types, such as realistic fiction, historical fiction, fantasy, fables, and so on. Nonfiction texts are based on facts and are often written with the purpose of teaching something. Nonfiction can be narrowed down into text types, such as biographies, memoirs, articles, essays, and so on.

  The text you are going to write should lend itself to answer questions like: What is the genre of this text? What characteristics help identify the genre? How does the genre of one text compare to another? How does the genre of the text help identify the author's purpose?
  """,
        "location details":
        """A thing that the readers will be assessed on is their ability to identify and describe the explicit details in the text. When answering text-dependent questions, students can cite text evidence by using dialogue frames such as: According to the text __; The text tells me__; In paragraph __ it says __. If you ask these questions, tell the students that they should highlight the sentence in text where they can find the answer to the question. 

  The text you are going to write should lend itself to answer questions like:  Where can you find the answer to this question? In what paragraph can you find the answer? How do you know this is the answer? What evidence from the text supports your answer?
  """,
        "sequence":
        """A thing that the readers will be assessed on is their ability to identify and describe sequence events in the text. The actions in a story are arranged in a particular order, usually from beginning to end. The sequence of events is the description of the order in which events occur. Transition words, such as first, next, then, after, and finally, help organize a sequence.

  The text you are going to write should lend itself to answer questions like: What happened at the beginning? What happened in the middle? What happened at the end? What happened after __ or before __? Are there words that signal chronological order? Include some transition words in the text you will generate. 
  """,
        "main idea":
        """A thing that the readers will be assessed on is their ability to identify and describe the main idea in the text. Readers examine the main ideas and details of a text in order to fully understand it. The main idea is the general topic presented in a text. The details are the extra descriptions and information that help readers better understand the text. Each section in a text often has its own main idea and details.

  The text you are going to write should lend itself to answer questions like:  What is this text mostly about? What is the big, or main, idea? What details support the main idea? What details are most important to understand the main idea?
  """,
        "cause effect":
        """A thing that the readers will be assessed on is their ability to identify and describe cause and effect in the text. Effective readers are able to identify and understand cause-and-effect relationships in various texts.

  The text you are going to write should lend itself to answer questions like: Why did __ happen? What caused __ to occur? What was the effect of ____? How did __ cause __ to occur? How would things be different if __ had not taken place? What happened, and why did it happen? Focus on words that signal causes and effects, such as: cause of, effects of, reason why, leads to, therefore, as a result of, because, due to, thus, may be due to, for this reason, if __ then __, not only, but, so that, and consequently. Include some words that signal causes and effects in the text you will generate. 
  """,
        "compare contrast":
        """A thing that the readers will be assessed on is their ability to identify and describe compare and contrast in the text. A text organized to explain how things are alike and different is a compare-and-contrast text structure. Focus on words that signal comparisons and contrasts, such as: like, also, both, unlike, in contrast, and, the same as, but, but also, on the other hand, instead of, as well as, similar to, different from, however, nevertheless, in comparison, and likewise.

  The text you are going to write should lend itself to answer questions like:  Why did the author use this text structure? And how knowing the text is written in a compare-and-contrast text structure helps readers predict, question, and anticipate what they will learn.
  """,
        "problem solution":
        """A thing that the readers will be assessed on is their ability to identify and describe the problem and solution in the text. In most stories, a character is confronted with a problem that needs to be solved. The problem is a challenge that must be worked out or solved, and the solution is the action or process used to resolve the problem. Words that signal problems and solutions are: the problem is, one solution is, dilemma, solve, issue, trouble, fix, how, however, therefore, as a result, consequently, so that, and nevertheless.

  The text you are going to write should lend itself to answer questions like: What is the problem or challenge in the story? How does the problem affect the characters? How is the problem solved? What is the solution? Is there more than one problem and solution in the story? Find text evidence about the problem and solutions. Have students identify the problem, possible solutions, actual solutions, and supporting evidence in a new text. Include some words that signal problems and solutions in the text you will generate. 
  """,
        "story elements":
        """A thing that the readers will be assessed on is their ability to identify and describe the story elements in the text. Elements of a story (characters, setting, plot, and theme) provide a framework for understanding a story. Understanding each separately and how they combine to tell a story helps students deepen their understanding.

  The text you are going to write should lend itself to answer questions like: Who are the characters? What is the setting? What is the problem? What events lead to the solution? What is the message or meaning of the story? What was the lesson the author wanted the characters or readers to learn? The problem or challenge faced by the characters and how the events that lead up to the solution affect the characters.
  """,
        "poetry":
        """A thing that the readers will be assessed on is their ability to identify and describe the poetry in the text. Poetry can be defined as a literary work that uses a distinct style and rhythm. Poetry is often organized in stanzas rather than paragraphs. Not all poems rhyme, although many do. Those that rhyme have a rhyming pattern that is usually consistent throughout the poem. Poetry can be written in many forms, such as haiku, free verse, sonnets, acrostic, limerick, and so on

  The poem you are going to write should lend itself to answer questions like: How is the poem organized? Does the poem rhyme? What type of poem is it? How does poetry compare to other text types? What are the common characteristics of poetry? What elements of poetry does the poem include? What is the meaning of this poem? Why did the author choose to write this text as a poem?
  """,
        "theme":
        """A thing that the readers will be assessed on is their ability to identify and describe the theme in the text. Fictional stories have important elements that shape the narrative: characters, setting, plot, and theme. The theme is the author's message. Readers can determine the theme by making inferences and identifying a message or lesson that can be applied to anyone. Theme is not story-specific. A story can have more than one theme.  For example, courage, friendship, loyalty, perseverance, acceptance, cooperation, honesty, kindness, and so on.

  The text you are going to write should lend itself to answer questions like: What is the author's message in this text? What is the theme of this text? How is it different from the main idea? How can you apply this to your own life? How did the author change at the end of the story? 
  """,
        "narrative":
        """A thing that the readers will be assessed on is their ability  to identify and describe the narrative point of view in the text. Stories are told from a specific point of view, usually in the first or third person. Readers can determine the point of view by deciding who is telling the story. In a first-person story, the narrator is one of the characters telling the story directly, using pronouns such as I and my. In a third-person story, a narrator tells the story indirectly by describing the characters and their thoughts and actions.

  The text you are going to write should lend itself to answer questions like:  Who is telling the story? From what point of view (first, second, or third person) is the story being told? Does the point of view change throughout the story, and how do you know? How would the story change if it were being told from another character's point of view? Explain the differences in each character's point of view. DO NOT INFORM THE READER ABOUT THE NARRATIVE, JUST WRITE IT IN A CERTAIN NARRATIVE AND HAVE THEM FIGURE OUT THE REST. 
  """,
    }

def get_query(writing_topics, topic, lexile_level):
  query = textwrap.dedent(
        f"""You are a professional writer. You are going to write an interesting text about {topic} that could be part of a book, a short story, a newspaper article or anything else. Students will read the text, so it should be safe to read for minors. 
                            Carefully follow the instructions below. Make sure that you keep the instructions below implicit. 
                            The students need to find out what the instructions are. So write the text following them, but do not give anything away by explicitly stating what instruction you are following. 
  Be very mindfull, the text should be written at the following lexile level: {lexile_level}.  Make the text about 500 words please too.

  {writing_topics}
                          
  Return a JSON format for the file, with a key named title for the title of the story and a key named text for the text content included and also a key named image with a string for a description of an image relating to the text. THE IMAGE KEY IS VERY IMPORTANT
  PLEASE DO NOT FORGET IT... DO NOT RETURN A RESPONSE UNTIL YOU'RE 100% SURE THE KEY IS INCLUDED.                         
    ONLY OUTPUT THE STORY! NOTHING ELSE
    DO NOT COPY THE STORYLINES FROM THE FILES I WILL FEED YOU. DO NOT REPRODUCE THE SAME STORYLINES OR GET THEMES FROM THEM.
    ESPECIALLY DO NOT MAKE A STORY ABOUT SLAVERY WHEN IT'S COMPLETELY UNRELATED TO THE TOPIC THE STUDENT ASKED FOR. THIS IS A STORY FOR KIDS, PLEASE MAKE APPROPRIATE AND SAFE.
  """)
  return query
strategy_for_questions = {
        "visualize":
        """The reading strategy that the student used is “Visualize”. The purpose is to let the student understand that effective readers visualize, or create pictures in their mind, as they read. These visualizations allow students to connect to the text in order to better remember and enjoy what they read. Visualizing also helps readers make sense of what they read so they deepen their comprehension of the text. You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above.  """,
        "summarize":
        """The reading strategy that the student used is “summarize”. The purpose is to let the student understand that effective readers summarize paragraphs, sections, or chapters as they read in order to better understand and remember material from a text. Summarizing allows students to use their own words to recall the main ideas of a text. Nudge the student to be able to answer the questions who, what, when, where, and why about a topic. You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above.  """,
        "prior knowledge":
        """The reading strategy that the student used is “Connect to Prior Knowledge”. The purpose is to let the students understand that effective readers make connections between what they already know and new texts they read. This connection gives readers a solid foundation to build upon while also contextualizing the new material they are reading. Remind students that thinking about what they already know about the topic of a text before reading will help them better understand and remember the new material. As they learn new information while reading, students will make deeper connections to what they already know. You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above.  """,
        "self monitor":
        """The reading strategy that the student used is “Self Monitor”. The purpose is to let the student understand that effective readers self-monitor their own reading by rereading, connecting to prior knowledge, looking for picture clues, and asking questions when understanding breaks down. Model periodic retelling and summarizing as a strategy for self-monitoring. Model questions that will help students make sense of the text. For example: Does this make sense? What is the author trying to tell me? What is happening? You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above.  """,
        "retell":
        """The reading strategy that the student used is “Retell”. The purpose is to let the student understand that effective readers stop occasionally while reading to retell in their minds what is happening in the text. Retelling allows students to grow their thinking and visualization skills so they are better able to remember what happened in the text. Relying on story sequence and characters' actions helps students retell what they have read. You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above.  """,
        "annotate":
        """The reading strategy that the student used is “Annotate”. The purpose is to let the student understand that effective readers annotate, or "mark up" texts, as they read. These notes allow readers to make connections, clarify important information, and keep track of questions while reading. Annotating also makes it easier for readers to refer to evidence when answering text-dependent questions and writing summaries. Annotating helps students keep track of ideas and questions, construct questions, and process key ideas. You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above. In the questions you ask, some should entail finding the answer in the text or with annotation. Tell them to highlight the answer to the question in the text.  """,
        "predictions":
        """The reading strategy that the student used is “Annotate”. The purpose is to let the student understand that effective readers make predictions, or logical guesses, about what will happen next in a text. Then they revise and/or confirm those predictions while reading. This strategy helps readers stay engaged with the material while also supporting comprehension. Model how to stop and make a prediction and think aloud about the part of the text your prediction is based upon. Continue to read and stop when the prediction is confirmed or revealed to be incorrect. Revise your prediction if needed. You should nudge the student to use this approach while answering the questions focusing on the comprehension points mentioned above. """,
    }

metrics_for_questions = {
        "genre":
        """The student is learning to identify and describe the characteristics of the genre. The term genre is also known as the type of text and is often categorized as fiction or nonfiction. Fiction texts are often presented in the form of stories with characters and a plot. Fiction can also be narrowed down into text types, such as realistic fiction, historical fiction, fantasy, fables, and so on. Nonfiction texts are based on facts and are often written with the purpose of teaching something. Nonfiction can be narrowed down into text types, such as biographies, memoirs, articles, essays, and so on.

  You should ask questions like: What is the genre of this text? What characteristics help identify the genre? How does the genre of one text compare to another? How does the genre of the text help identify the author's purpose?

  Come up with a total of 3 questions for genre. 
  """,
        "location details":
        """The student is learning to identify and describe the explicit details in the text. When answering text-dependent questions, students can cite text evidence by using dialogue frames such as: According to the text __; The text tells me__; In paragraph __ it says __. If you ask these questions, tell the students that they should highlight the sentence in text where they can find the answer to the question. 

  You should ask questions like: Where can you find the answer to this question? In what paragraph can you find the answer? How do you know this is the answer? What evidence from the text supports your answer?

  Come up with a total of 5 questions for explicit details. 
  """,
        "sequence":
        """The student is learning to identify and describe sequence events in the text. The actions in a story are arranged in a particular order, usually from beginning to end. The sequence of events is the description of the order in which events occur. Transition words, such as first, next, then, after, and finally, help organize a sequence.

  You should ask questions like: What happened at the beginning? What happened in the middle? What happened at the end? What happened after __ or before __? Are there words that signal chronological order? For the latter questions, where there are words that signal chronological order, have the student highlight them in the text for one of the questions. 

  Come up with a total of 4 questions for sequence events.
  """,
        "main idea":
        """The student is learning to identify and describe the main idea in the text. Readers examine the main ideas and details of a text in order to fully understand it. The main idea is the general topic presented in a text. The details are the extra descriptions and information that help readers better understand the text. Each section in a text often has its own main idea and details.

  You should ask questions like: What is this text mostly about? What is the big, or main, idea? What details support the main idea? What details are most important to understand the main idea?

  Come up with a total of 4 questions for main idea
  """,
        "cause effect":
        """The student is learning to identify and describe cause and effect in the text. Effective readers are able to identify and understand cause-and-effect relationships in various texts.

  You should ask questions like: Why did __ happen? What caused __ to occur? What was the effect of ____? How did __ cause __ to occur? How would things be different if __ had not taken place? What happened, and why did it happen? Focus on words that signal causes and effects, such as: cause of, effects of, reason why, leads to, therefore, as a result of, because, due to, thus, may be due to, for this reason, if __ then __, not only, but, so that, and consequently.

  Come up with a total of 4 questions for cause and effect. 
  """,
        "compare contrast":
        """The student is learning to identify and describe compare and contrast in the text. A text organized to explain how things are alike and different is a compare-and-contrast text structure. Focus on words that signal comparisons and contrasts, such as: like, also, both, unlike, in contrast, and, the same as, but, but also, on the other hand, instead of, as well as, similar to, different from, however, nevertheless, in comparison, and likewise.

  With your questions focus on: Why did the author use this text structure? And how knowing the text is written in a compare-and-contrast text structure helps readers predict, question, and anticipate what they will learn.

  Come up with a total of 4 questions for compare and contrast
  """,
        "problem solution":
        """The student is learning to identify and describe the problem and solution in the text. In most stories, a character is confronted with a problem that needs to be solved. The problem is a challenge that must be worked out or solved, and the solution is the action or process used to resolve the problem. Words that signal problems and solutions are: the problem is, one solution is, dilemma, solve, issue, trouble, fix, how, however, therefore, as a result, consequently, so that, and nevertheless.

  You should ask questions like: What is the problem or challenge in the story? How does the problem affect the characters? How is the problem solved? What is the solution? Is there more than one problem and solution in the story? Find text evidence about the problem and solutions. Have students identify the problem, possible solutions, actual solutions, and supporting evidence in a new text. 

  Come up with a total of 4 questions for problem-solution
  """,
        "story elements":
        """The student is learning to identify and describe the story elements in the text. Elements of a story (characters, setting, plot, and theme) provide a framework for understanding a story. Understanding each separately and how they combine to tell a story helps students deepen their understanding.

  You should ask questions like: Who are the characters? What is the setting? What is the problem? What events lead to the solution? What is the message or meaning of the story? What was the lesson the author wanted the characters or readers to learn? The problem or challenge faced by the characters and how the events that lead up to the solution affect the characters.

  Come up with a total of 5 questions for story elements
  """,
        "poetry":
        """The student is learning to identify and describe the poetry in the text. Poetry can be defined as a literary work that uses a distinct style and rhythm. Poetry is often organized in stanzas rather than paragraphs. Not all poems rhyme, although many do. Those that rhyme have a rhyming pattern that is usually consistent throughout the poem. Poetry can be written in many forms, such as haiku, free verse, sonnets, acrostic, limerick, and so on

  Ask questions like: How is the poem organized? Does the poem rhyme? What type of poem is it? How does poetry compare to other text types? What are the common characteristics of poetry? What elements of poetry does the poem include? What is the meaning of this poem? Why did the author choose to write this text as a poem?

  Come up with a total of 5 questions for poetry
  """,
        "theme":
        """The student is learning to identify and describe the theme in the text. Fictional stories have important elements that shape the narrative: characters, setting, plot, and theme. The theme is the author's message. Readers can determine the theme by making inferences and identifying a message or lesson that can be applied to anyone. Theme is not story-specific. A story can have more than one theme.  For example, courage, friendship, loyalty, perseverance, acceptance, cooperation, honesty, kindness, and so on.

  Ask questions like: What is the author's message in this text? What is the theme of this text? How is it different from the main idea? How can you apply this to your own life? How did the author change at the end of the story? 

  Come up with a total of 5 questions for poetry
  """,
        "narrative":
        """The student is learning to identify and describe the narrative point of view in the text. Stories are told from a specific point of view, usually in the first or third person. Readers can determine the point of view by deciding who is telling the story. In a first-person story, the narrator is one of the characters telling the story directly, using pronouns such as I and my. In a third-person story, a narrator tells the story indirectly by describing the characters and their thoughts and actions.

  Ask questions like: Who is telling the story? From what point of view (first, second, or third person) is the story being told? Does the point of view change throughout the story, and how do you know? How would the story change if it were being told from another character's point of view? Explain the differences in each character's point of view.

  Come up with a total of 4 questions for poetry
  """,
        "descriptive":
        """The student is learning to identify and describe the descriptive features in the text. A text that is organized with a descriptive or informational text structure organizes information by describing the attributes and details of a person, place, thing, idea, or event. The author presents a main idea, divides the text into related subtopics, and then supports the text with informational details. Descriptive text might use sensory details because they allow readers to visualize as they read.

  Ask questions like: Why did the author use this text structure? What can you learn from this structure? And focus on words that are typical for this type of text: for example, such as, most importantly, specifically, in addition, for instance, to illustrate, described as, another, is like, and including.

  Come up with a total of 4 questions for descriptive texts.
  """,
    }