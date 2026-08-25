import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { PublicRoute } from './components/PublicRoute';
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { ForgotPassword } from './pages/ForgotPassword';
import { ResetPassword } from './pages/ResetPassword';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/dashboard/Overview';
import { PaymentsPage } from './pages/dashboard/PaymentsPage';
import { RecoveryCasesPage } from './pages/dashboard/RecoveryCasesPage';
import { AiDecisionsPage } from './pages/dashboard/AiDecisionsPage';
import { SimulatorPage } from './pages/dashboard/SimulatorPage';
import { CustomersPage } from './pages/dashboard/CustomersPage';
import { AnalyticsPage } from './pages/dashboard/AnalyticsPage';
import { SettingsPage } from './pages/dashboard/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/signup"
            element={
              <PublicRoute>
                <SignUp />
              </PublicRoute>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <PublicRoute>
                <ForgotPassword />
              </PublicRoute>
            }
          />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Protected Merchant Workspace & Dashboard Routes */}
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/app/overview" replace />} />
            <Route path="overview" element={<Overview />} />
            <Route path="payments" element={<PaymentsPage />} />
            <Route path="recovery-cases" element={<RecoveryCasesPage />} />
            <Route path="ai-decisions" element={<AiDecisionsPage />} />
            <Route path="simulator" element={<SimulatorPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Root Redirect */}
          <Route path="/" element={<Navigate to="/app/overview" replace />} />

          {/* Catch-all Wildcard */}
          <Route path="*" element={<Navigate to="/app/overview" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
