import {
    useBlockNoteEditor,
    useComponentsContext,
    useEditorContentOrSelectionChange,
    useSelectedBlocks,
  } from "@blocknote/react";
  import "@blocknote/mantine/style.css";
  import { useCallback, useMemo, useState } from "react";
  import { MdComment } from "react-icons/md";
  import {
    CommentNewSubmitButton,
    CommentNewTextarea,
    useCommentsSelectors,
  } from '@udecode/plate-comments';
  import { cn } from '@udecode/cn';
  import { inputVariants } from './input';
  import { buttonVariants } from './button';
  
  // Helper function to check if the comment is in the schema
  function checkCommentInSchema(editor) {
    return (
      "comment" in editor.schema.styleSpecs &&
      editor.schema.styleSpecs["comment"].config.type === "comment"
    );
  }
  
  export const BlueButton = () => {
    const editor = useBlockNoteEditor();
    const Components = useComponentsContext()!;
  
    const commentInSchema = checkCommentInSchema(editor);
    const [active, setActive] = useState("comment" in editor.getActiveStyles());
  
    useEditorContentOrSelectionChange(() => {
      if (commentInSchema) {
        setActive("comment" in editor.getActiveStyles());
      }
    }, editor);
  
    const selectedBlocks = useSelectedBlocks(editor);
  
    const getSelectedComment = () => {
      return editor._tiptapEditor.getAttributes("comment").stringValue || "";
    };
  
    const [comment, setComment] = useState(getSelectedComment());
    const [text, setText] = useState(editor.getSelectedText());
  
    useEditorContentOrSelectionChange(() => {
      setText(editor.getSelectedText() || "");
      setComment(getSelectedComment() || "");
    }, editor);
  
    const update = useCallback(
      (comment) => {
        editor.addStyles({ comment });
        editor.focus();
        editor.domElement.focus();
      },
      [editor]
    );
  
    const onDelete = useCallback(() => {
      editor.removeStyles({ comment: "" });
    }, [editor]);
  
    const show = useMemo(() => {
      if (!commentInSchema) {
        return false;
      }
  
      for (const block of selectedBlocks) {
        if (block.content === undefined) {
          return false;
        }
      }
  
      return true;
    }, [commentInSchema, selectedBlocks]);
  
    const [isPopupVisible, setIsPopupVisible] = useState(false);
    const [inputText, setInputText] = useState("");
  
    const handleButtonClick = () => {
      if (text) {
        setInputText(comment); // Set inputText to the current comment
        setIsPopupVisible(true);
      } else {
        // Toggle comment style if no text is selected
        setIsPopupVisible(false);
      }
    };
  
    const handlePopupSubmit = () => {
      update(inputText);
      setIsPopupVisible(false);
    };
  
    if (!show) {
      return null;
    }
  
    return (
      <>
        <div className="toolbar-container">
          <Components.FormattingToolbar.Button
            mainTooltip={"Create Comment"}
            onClick={handleButtonClick}
            isSelected={active}
            icon={MdComment}
          >
            Comment
          </Components.FormattingToolbar.Button>
        </div>
  
        {isPopupVisible && (
          <form className="popup" onSubmit={handlePopupSubmit}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter your comment"
          />
          <button type="submit" disabled={inputText.trim().length === 0}>Submit</button>
        </form>
        )}
  
        <style jsx>{`
          .toolbar-container {
            display: flex;
          }
          .popup {
            position: absolute;
            top: 60px; /* Adjust this value as needed */
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border: 1px solid #ccc;
            padding: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
          }
          .testing {
            position: relative;
            display: inline-block;
            cursor: pointer;
          }
  
          .testing:hover .comment-tooltip {
            display: block;
          }
  
          .comment-tooltip {
            display: none;
            position: absolute;
            top: 100%; /* Adjust if you want the tooltip above the span */
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border: 1px solid #ccc;
            padding: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            white-space: nowrap;
          }
        `}</style>
      </>
    );
  };
  
  // Usage example to add the highlight and tooltip
  const HighlightWithTooltip = ({ text, comment }) => (
    <span className="testing" data-value={comment}>
      {text}
      <div className="comment-tooltip">{comment}</div>
    </span>
  );
  