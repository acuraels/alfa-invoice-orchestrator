import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminPanelPage } from './pages/AdminPanelPage/AdminPanelPage';
import { InvoiceDetailsPage } from './pages/InvoiceDetailsPage/InvoiceDetailsPage';
import { InvoiceListPage } from './pages/InvoiceListPage/InvoiceListPage';
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
        <Route path="/" element={<Navigate to="/invoice-list" replace />} />
        <Route path="/login" element={<LogInPage />} />
        <Route path="/logout" element={<LogOutPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        <Route path="/invoice-list" element={<InvoiceListPage />} />
        <Route path="/invoice-list/:id" element={<InvoiceDetailsPage />} />

        <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
          <Route path="/admin-panel" element={<AdminPanelPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
