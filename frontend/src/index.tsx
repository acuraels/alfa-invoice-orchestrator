import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const rootElement = document.getElementById("root") as HTMLElement;
const reactRoot = createRoot(rootElement);

reactRoot.render(
  <StrictMode>
    <App />
  </StrictMode>
);
