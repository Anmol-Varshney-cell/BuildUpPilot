import { Navigate, Route, Routes } from "react-router-dom";
import ProblemListPage from "./pages/ProblemListPage";
import ProblemDetailPage from "./pages/ProblemDetailPage";
import ProfilePage from "./pages/ProfilePage";
import SubmissionsPage from "./pages/SubmissionsPage";
import JourneysPage from "./pages/JourneysPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ProblemListPage />} />
      <Route path="/problems" element={<ProblemListPage />} />
      <Route path="/problems/:slug" element={<ProblemDetailPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/submissions" element={<SubmissionsPage />} />
      <Route path="/journeys" element={<JourneysPage />} />
      <Route path="*" element={<Navigate to="/problems" replace />} />
    </Routes>
  );
}
