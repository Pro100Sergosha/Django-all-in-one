import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000/",
});

export async function helloWorld() {
  const res = await api.get("api/");
  return res.data;
}
