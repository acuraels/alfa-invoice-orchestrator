import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
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
          duration: 3000,
          className: 'app-toast',
        }}
      />
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LogInPage />} />
        <Route path="/logout" element={<LogOutPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
