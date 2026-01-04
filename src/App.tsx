import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import WelcomeView from "./views/WelcomeView";
import IngestionView from "./views/IngestionView";
import AnalysisView from "./views/AnalysisView";
import MainLayout from "./layouts/MainLayout";
import { useStore } from "./store/useStore";

function App() {
  const { authStatus } = useStore();

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            authStatus === "authenticated" ? (
              <Navigate to="/ingestion" />
            ) : (
              <WelcomeView />
            )
          }
        />

        <Route
          path="/ingestion"
          element={
            authStatus === "authenticated" ? (
              <MainLayout>
                <IngestionView />
              </MainLayout>
            ) : (
              <Navigate to="/" />
            )
          }
        />

        <Route
          path="/analysis"
          element={
            authStatus === "authenticated" ? (
              <MainLayout>
                <AnalysisView />
              </MainLayout>
            ) : (
              <Navigate to="/" />
            )
          }
        />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
