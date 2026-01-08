import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import WelcomeView from "./views/WelcomeView";
import IngestionView from "./views/IngestionView";
import AnalysisView from "./views/AnalysisView";
import MissingDatesView from "./views/MissingDatesView";
import DuplicatesView from "./views/DuplicatesView";
import StorageMetadataView from "./views/StorageMetadataView";
import ProcessMetadataView from "./views/ProcessMetadataView";
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

        <Route
          path="/analysis/missing-dates"
          element={
            authStatus === "authenticated" ? (
              <MainLayout>
                <MissingDatesView />
              </MainLayout>
            ) : (
              <Navigate to="/" />
            )
          }
        />

        <Route
          path="/analysis/duplicates"
          element={
            authStatus === "authenticated" ? (
              <MainLayout>
                <DuplicatesView />
              </MainLayout>
            ) : (
              <Navigate to="/" />
            )
          }
        />

        <Route
          path="/analysis/storage-metadata"
          element={
            authStatus === "authenticated" ? (
              <MainLayout>
                <StorageMetadataView />
              </MainLayout>
            ) : (
              <Navigate to="/" />
            )
          }
        />

        <Route
          path="/analysis/process-metadata"
          element={
            authStatus === "authenticated" ? (
              <MainLayout>
                <ProcessMetadataView />
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
