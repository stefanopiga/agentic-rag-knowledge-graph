
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout, ProtectedRoute, PublicRoute } from "@/components/layout";
import { ChatPage, LoginPage } from "@/pages";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/chat" replace />,
  },
  {
    path: "/login",
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: "chat",
        element: <ChatPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/chat" replace />,
  },
]);
