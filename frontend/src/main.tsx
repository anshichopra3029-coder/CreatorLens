import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AuthProvider } from "./auth/AuthProvider.tsx";
import App from "./App.tsx";
import "./index.css";

const root = document.getElementById("root");
if (!root) {
  throw new Error("The page is missing the root element.");
}

createRoot(root).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
);
