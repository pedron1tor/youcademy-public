'use client';

import React from 'react';

import { cn } from '@udecode/cn';
import {
  useCommentDeleteButton,
  useCommentDeleteButtonState,
  useCommentEditButton,
  useCommentEditButtonState,
} from '@udecode/plate-comments';

import { Icons } from '@/components/icons';

import { Button } from './button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './dropdown-menu';

export function CommentMoreDropdown() {
  const editButtonState = useCommentEditButtonState();
  const { props: editProps } = useCommentEditButton(editButtonState);
  const deleteButtonState = useCommentDeleteButtonState();
  const { props: deleteProps } = useCommentDeleteButton(deleteButtonState);

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button className={cn('h-6 p-1 text-slate-500 dark:text-slate-400')} variant='ghost'>
          <Icons.more className='size-4' />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem {...editProps}>Edit comment</DropdownMenuItem>
        <DropdownMenuItem {...deleteProps}>Delete comment</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
