import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import HomePageNew from "./pages/HomePageNew";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProfilePage from "./pages/ProfilePage";
import Dashboard from "./pages/Dashboard";
import PaymentSuccess from "./pages/PaymentSuccess";
import PaymentCancel from "./pages/PaymentCancel";
import ApiKeys from "./pages/ApiKeys";
import Webhooks from "./pages/Webhooks";
import ErpIntegrations from "./pages/ErpIntegrations";
import Analytics from "./pages/Analytics";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import DisclaimerPage from "./pages/Disclaimer";
import CookiePolicy from "./pages/CookiePolicy";
import DataProcessingAgreement from "./pages/DataProcessingAgreement";
import License from "./pages/License";
import V4SearchPage from "./pages/V4SearchPage";

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Routes>
            <Route path="/" element={<HomePageNew />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/v4"
              element={
                <ProtectedRoute>
                  <V4SearchPage />
                </ProtectedRoute>
              }
            />
            <Route path="/payment/success" element={<PaymentSuccess />} />
            <Route path="/payment/cancel" element={<PaymentCancel />} />
            <Route
              path="/api-keys"
              element={
                <ProtectedRoute>
                  <ApiKeys />
                </ProtectedRoute>
              }
            />
            <Route
              path="/webhooks"
              element={
                <ProtectedRoute>
                  <Webhooks />
                </ProtectedRoute>
              }
            />
            <Route
              path="/erp-integrations"
              element={
                <ProtectedRoute>
                  <ErpIntegrations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />
            <Route path="/vop" element={<TermsOfService />} />
            <Route path="/terms" element={<TermsOfService />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/disclaimer" element={<DisclaimerPage />} />
            <Route path="/cookies" element={<CookiePolicy />} />
            <Route path="/dpa" element={<DataProcessingAgreement />} />
            <Route path="/license" element={<License />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
