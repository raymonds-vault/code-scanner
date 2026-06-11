import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.tsx";
import Dashboard from "./pages/Dashboard.tsx";
import Knowledge from "./pages/Knowledge.tsx";
import Login from "./pages/Login.tsx";
import ScanDetail from "./pages/ScanDetail.tsx";
import ProtectedRoute from "./components/ProtectedRoute.tsx";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/scans/:id"
            element={
              <ProtectedRoute>
                <ScanDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/knowledge"
            element={
              <ProtectedRoute>
                <Knowledge />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
