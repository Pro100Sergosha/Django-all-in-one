import { useEffect, useState } from "react";
import { helloWorld } from "../services/api";

export default function Home() {
  const [message, setMessage] = useState("Loading...");
  const [error, setError] = useState(null);

  useEffect(() => {
    helloWorld()
      .then((data) => setMessage(data.message))
      .catch(() => setError("Error fetching data"));
  }, []);
  return (
    <div className="p-8 text-xl">
      <h1 className="text-2xl font-bold">Home Page</h1>
      <p>{message}</p>
      {error && <p className="text-red-500">{error}</p>}
    </div>
  );
}
