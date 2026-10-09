/**
 * This file contains the implementation of the main App component of the editor.
 * The App component is responsible for rendering the BlockNoteView component,
 * which is a rich text editor powered by the BlockNote library.
 * It also handles fetching and updating the editor content from the server,
 * as well as uploading files to GCP.
 */

import React, { useEffect, useState, useRef } from "react";
import axios from 'axios';
import "@blocknote/core/fonts/inter.css";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView, Theme } from "@blocknote/mantine";
import "@blocknote/mantine/style.css";
import { v4 as uuidv4 } from 'uuid'; // Import UUID generator

// Utility function to get CSRF token
const getCsrfToken = () => {
  const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
  return csrfMetaTag ? csrfMetaTag.getAttribute('content') : '';
};

// Utility function to get app URL and parameters
const getAppData = () => {
  const appElement = document.getElementById('react-app');
  if (appElement) {
    const userId = appElement.getAttribute('data-user-id');
    const qid = appElement.getAttribute('data-qid');
    const url = appElement.getAttribute('data-url') || '';
    return { userId, qid, url, params: { qid, userId } };
  }
  return { userId: '', qid: '', url: '', params: {} };
};

const appData = getAppData(); // Fetch once and reuse

// Utility function to upload a file to the Django backend
const uploadFile = async (file: File) => {
  const imageMimeTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  if (!imageMimeTypes.includes(file.type)) {
    console.error('File is not an image');
    return Promise.reject('File is not an image'); // Reject the promise if the file is not an image
  }
  const uuid = uuidv4(); // Generate UUID in frontend
  const csrfToken = getCsrfToken();
  const body = new FormData();

  body.append("file", file);
  body.append("doc_id", uuid);
  body.append("user_id", appData.userId);
  body.append("qid", appData.qid);

  const response = await axios.post(`${appData.url}/api/upload_image/`, body, {
    headers: {
      "Content-Type": "multipart/form-data",
      'X-CSRFToken': csrfToken,
    },
  });
  return response.data.file_url;
};

const EditorComponent = ({ initialContent }) => {
  const hasContent = initialContent && initialContent.length > 0;
  const [blocks, setBlocks] = useState(hasContent ? initialContent : []);
  const [deletedBlockIds, setDeletedBlockIds] = useState<string[]>([]);
  const editorOptions = hasContent ? { initialContent: blocks, uploadFile } : { uploadFile };
  const editor = useCreateBlockNote(editorOptions);
  const blocksRef = useRef(blocks);

  useEffect(() => {
    blocksRef.current = blocks;
  }, [blocks]);

  useEffect(() => {
    const sendBlocksToServer = () => {
      const csrfToken = getCsrfToken();

      if (!csrfToken) {
        console.error('CSRF token not found');
        return;
      }

      axios.post(`${appData.url}/api/update-editor-content/`, 
        { 
          blocks: blocksRef.current,
          user_id: appData.userId,
          qid: appData.qid 
        }, 
        {
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
        }
      )
      .then(response => {
        console.log('Successfully saved', response);
      })
      .catch(error => {
        console.error('Failed to save editor data', error);
      });
    };

    sendBlocksToServer();
  }, [blocks, appData]);

  const handleEditorChange = () => {
    if (editor && editor.document) {
      const currentBlocks = editor.document;

      const currentBlockIds = currentBlocks.map(block => block.id);
      const deletedIds = blocksRef.current.filter(block => !currentBlockIds.includes(block.id)).map(block => block.id);

      setDeletedBlockIds(prev => [...new Set([...prev, ...deletedIds])]);
      setBlocks(currentBlocks);
    }
  };

  const lightWithBlack = {
    colors: {
      editor: {
        text: "#000000",
        background: "#FFFFFF",
      },
      menu: {
        text: "#3f3f3f",
        background: "#ffffff",
      },
      tooltip: {
        text: "#3f3f3f",
        background: "#efefef",
      },
      hovered: {
        text: "#3f3f3f",
        background: "#efefef",
      },
      selected: {
        text: "#ffffff",
        background: "#3f3f3f",
      },
      disabled: {
        text: "#afafaf",
        background: "#efefef",
      },
      shadow: "#cfcfcf",
      border: "#efefef",
      sideMenu: "#cfcfcf",
      highlights: {
        gray: {
          text: "#9b9a97",
          background: "#ebeced",
        },
        brown: {
          text: "#64473a",
          background: "#e9e5e3",
        },
        red: {
          text: "#e03e3e",
          background: "#fbe4e4",
        },
        orange: {
          text: "#d9730d",
          background: "#f6e9d9",
        },
        yellow: {
          text: "#dfab01",
          background: "#fbf3db",
        },
        green: {
          text: "#4d6461",
          background: "#ddedea",
        },
        blue: {
          text: "#0b6e99",
          background: "#ddebf1",
        },
        purple: {
          text: "#6940a5",
          background: "#eae4f2",
        },
        pink: {
          text: "#ad1a72",
          background: "#f4dfeb",
        },
      },
      fontFamily: "Roboto",
    },
  } satisfies Theme;

  const blackTheme = {
    light: lightWithBlack,
    dark: lightWithBlack,
  };

  return <BlockNoteView editor={editor} theme={blackTheme} onChange={handleEditorChange} />;
};

const App = () => {
  const [initialData, setInitialData] = useState(null);
  const [isLoading, setIsLoading] = useState(true); // Introduce a loading state

  useEffect(() => {
    setIsLoading(true); // Start loading
    axios.get(`${appData.url}/api/get-editor-content/`, { params: appData.params })
      .then(response => {
        setInitialData(response.data.initialContent);
        setIsLoading(false); // Data fetched, loading complete
      })
      .catch(error => {
        console.error('Failed to fetch initial data for the editor', error);
        setIsLoading(false); // Fetching failed, loading complete
      });
  }, []);

  return (
    <div>
      {isLoading ? (
        <div>Loading...</div> // Show loading indicator while data is being fetched
      ) : initialData !== null ? (
        <EditorComponent initialContent={initialData} /> // Data fetched successfully
      ) : (
        <div>Failed to load data</div> // Fetching failed or data is null
      )}
    </div>
  );
};

export default App;
