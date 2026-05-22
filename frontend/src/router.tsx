import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "./views/AppShell";
import { NoteEditorPage } from "./views/NoteEditorPage";
import { NoteListPage } from "./views/NoteListPage";
import { SharedNotePage } from "./views/SharedNotePage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <NoteListPage /> },
      { path: "notes/new", element: <NoteEditorPage mode="create" /> },
      { path: "notes/:noteId/edit", element: <NoteEditorPage mode="edit" /> },
    ],
  },
  {
    path: "/s/:token",
    element: <SharedNotePage />,
  },
]);
