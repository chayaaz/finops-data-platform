const BASE_URL = "http://127.0.0.1:8000";

export async function fetchSummary() {
  const response = await fetch(`${BASE_URL}/summary`);
  return response.json();
}

export async function fetchRaw() {
  const response = await fetch(`${BASE_URL}/raw`);
  return response.json();
}

export async function fetchClean() {
  const response = await fetch(`${BASE_URL}/clean`);
  return response.json();
}

export async function fetchIssues() {
  const response = await fetch(`${BASE_URL}/issues`);
  return response.json();
}