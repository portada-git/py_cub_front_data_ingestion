import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { useStore } from "./store/useStore";

// Component to initialize auth check
function AppWithAuthCheck() {
  const { checkAuth } = useStore();
  
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  
  return <App />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppWithAuthCheck />
  </StrictMode>
);
