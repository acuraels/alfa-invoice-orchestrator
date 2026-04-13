import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppPage } from './pages/AppPage/AppPage';
import { LogInPage } from './pages/LogInPage/LogInPage';
import { LogOutPage } from './pages/LogOutPage/LogOutPage';
import { NotFoundPage } from './pages/NotFoundPage/NotFoundPage';
import { UnauthorizedPage } from './pages/UnauthorizedPage/UnauthorizedPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 2500,
          className: 'app-toast',
        }}
      />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LogInPage />} />
        <Route path="/logout" element={<LogOutPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<AppPage tab="dashboard" />} />
          <Route path="/raw-transactions" element={<AppPage tab="raw" />} />
          <Route path="/aggregation-groups" element={<AppPage tab="groups" />} />
          <Route path="/draft-invoices" element={<AppPage tab="drafts" />} />
          <Route path="/final-invoices" element={<AppPage tab="finals" />} />
          <Route path="/exports" element={<AppPage tab="exports" />} />
          <Route path="/errors" element={<AppPage tab="errors" />} />
          <Route path="/charts" element={<AppPage tab="charts" />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
