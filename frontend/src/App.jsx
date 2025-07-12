import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="p-4 bg-gray-800 text-white space-x-4">
        <Link to="/" className="hover:underline">
          Home
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}
