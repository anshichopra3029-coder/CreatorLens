import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./layouts/AppShell.tsx";
import { AnalyticsPage } from "./pages/AnalyticsPage.tsx";
import { DashboardPage } from "./pages/DashboardPage.tsx";
import { DocumentAnalysisPage } from "./pages/DocumentAnalysisPage.tsx";
import { DocumentsPage } from "./pages/DocumentsPage.tsx";
import { InsightsPage } from "./pages/InsightsPage.tsx";
import { LandingPage } from "./pages/LandingPage.tsx";
import { NotFoundPage } from "./pages/NotFoundPage.tsx";
import { PerformancePage } from "./pages/PerformancePage.tsx";
import { PredictionsPage } from "./pages/PredictionsPage.tsx";
import { SettingsPage } from "./pages/SettingsPage.tsx";
import { UploadPage } from "./pages/UploadPage.tsx";
import { YoutubeAnalysisPage } from "./pages/YoutubeAnalysisPage.tsx";
import { YoutubePage } from "./pages/YoutubePage.tsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/youtube" element={<YoutubePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/insights" element={<InsightsPage />} />
          <Route path="/predictions" element={<PredictionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/youtube/:analysisId" element={<YoutubeAnalysisPage />} />
          <Route path="/performance/:analysisId" element={<PerformancePage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/analysis/:documentId" element={<DocumentAnalysisPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
