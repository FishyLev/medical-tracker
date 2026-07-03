const API_BASE = "http://127.0.0.1:8000/api";

async function parseResponse(res, fallbackMessage) {
  if (res.ok) {
    return res.json();
  }

  let errorMessage = fallbackMessage;

  try {
    const data = await res.json();
    errorMessage =
      data.detail ||
      data.message ||
      JSON.stringify(data) ||
      fallbackMessage;
  } catch {
    try {
      const text = await res.text();
      errorMessage = text || fallbackMessage;
    } catch {
      errorMessage = fallbackMessage;
    }
  }

  throw new Error(errorMessage);
}

function authHeaders(token, extraHeaders = {}) {
  return {
    ...extraHeaders,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function createUser(payload, token) {
  const res = await fetch(`${API_BASE}/user`, {
    method: "POST",
    headers: authHeaders(token, { "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });

  return parseResponse(res, "Failed to create user");
}

export async function uploadDocument(userId, file, token) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/${userId}/upload`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });

  return parseResponse(res, "Failed to upload document");
}

export async function listDocuments(userId, token) {
  const res = await fetch(`${API_BASE}/documents/${userId}`, {
    method: "GET",
    headers: authHeaders(token),
  });

  return parseResponse(res, "Failed to load documents");
}

export async function sendMessage(payload, token) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: authHeaders(token, { "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });

  return parseResponse(res, "Failed to send message");
}

export async function signup(payload) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse(res, "Signup failed");
}

export async function login(payload) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse(res, "Login failed");
}