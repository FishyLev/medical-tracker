import ReactMarkdown from "react-markdown";
import { useEffect, useRef, useState } from "react";
import {
  createUser,
  listDocuments,
  login,
  signup,
  uploadDocument,
} from "./services/api";
import "./styles.css";

const urgencyConfig = {
  high: { label: "Get care now", className: "urgency-badge urgency-high" },
  medium: { label: "See care soon", className: "urgency-badge urgency-medium" },
  low: { label: "Self-care / routine", className: "urgency-badge urgency-low" },
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function sanitizeAssistantContent(raw) {
  if (!raw) return "";

  return String(raw)
    .replace(/\r\n/g, "\n")
    .replace(/\n\s*[-*+]\s*$/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export default function App() {
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const [token, setToken] = useState("");
  const [userId, setUserId] = useState("");

  const [authMode, setAuthMode] = useState("login");
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");

  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  const [error, setError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  async function handleAuthSubmit(e) {
    e.preventDefault();
    setError("");
    setAuthSuccess("");
    setAuthLoading(true);

    try {
      let data;

      if (authMode === "signup") {
        data = await signup({
          name: authName,
          email: authEmail,
          password: authPassword,
        });
      } else {
        data = await login({
          email: authEmail,
          password: authPassword,
        });
      }

      setToken(data.access_token || "");
      setUserId(data.user_id || "");
      setAuthSuccess(
        authMode === "signup"
          ? "Account created successfully"
          : "Logged in successfully"
      );
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleCreateUserProfile() {
    if (!token) return;
    if (userId) return;

    try {
      const data = await createUser(
        {
          name: name || authName || "User",
          age: age ? Number(age) : null,
          gender,
        },
        token
      );

      setUserId(data.user_id);
    } catch (err) {
      setError(err.message || "Failed to create user profile");
    }
  }

  async function refreshDocuments(currentUserId = userId) {
    if (!currentUserId || !token) return;

    try {
      const data = await listDocuments(currentUserId, token);
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message || "Failed to load documents");
    }
  }

  useEffect(() => {
    if (token && userId) {
      refreshDocuments(userId);
    }
  }, [token, userId]);

  useEffect(() => {
    if (token && !userId) {
      handleCreateUserProfile();
    }
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!token) {
      setError("Please log in first.");
      return;
    }

    if (!userId) {
      setError("User profile not ready yet.");
      return;
    }

    setUploading(true);
    setError("");
    setUploadSuccess("");

    try {
      const result = await uploadDocument(userId, file, token);
      console.log("Upload success:", result);
      await refreshDocuments(userId);
      setUploadSuccess(`${file.name} uploaded successfully`);

      if (fileInputRef.current) {
        fileInputRef.current.value = null;
      }
    } catch (err) {
      console.error("Upload failed:", err);
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleSendMessage() {
    if (!token) {
      setError("Please log in first.");
      return;
    }

    if (!userId) {
      setError("User profile not ready yet.");
      return;
    }

    if (!message.trim() || loading) return;

    const userText = message.trim();
    let assistantIndex = -1;

    setMessages((prev) => {
      assistantIndex = prev.length + 1;
      return [
        ...prev,
        { role: "user", content: userText },
        { role: "assistant", content: "", metadata: {}, streaming: true },
      ];
    });

    setMessage("");
    setLoading(true);
    setError("");
    setUploadSuccess("");

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          user_id: Number(userId),
          message: userText,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Streaming request failed");
      }

      if (!response.body) {
        throw new Error("Streaming not supported by browser");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      let streamedContent = "";
      let streamedMetadata = {};
      let finalPayload = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const event of events) {
          const lines = event
            .split("\n")
            .map((line) => line.trim())
            .filter(Boolean);

          for (const line of lines) {
            if (!line.startsWith("data:")) continue;

            const raw = line.slice(5).trim();
            if (!raw) continue;

            let parsed;
            try {
              parsed = JSON.parse(raw);
            } catch {
              continue;
            }

            if (parsed.type === "meta") {
              streamedMetadata = {
                ...streamedMetadata,
                session_id: parsed.session_id,
              };
            }

            if (parsed.type === "chunk") {
              streamedContent += parsed.content || "";

              setMessages((prev) =>
                prev.map((msg, idx) =>
                  idx === assistantIndex
                    ? {
                        ...msg,
                        content: sanitizeAssistantContent(streamedContent),
                        metadata: streamedMetadata,
                        streaming: true,
                      }
                    : msg
                )
              );
            }

            if (parsed.type === "done") {
              finalPayload = parsed.payload || null;

              const rawContent =
                finalPayload?.response ||
                finalPayload?.message ||
                finalPayload?.assistant_message ||
                finalPayload?.reply ||
                streamedContent;

              const cleanedContent = sanitizeAssistantContent(rawContent);

              setMessages((prev) =>
                prev.map((msg, idx) =>
                  idx === assistantIndex
                    ? {
                        ...msg,
                        content: cleanedContent,
                        metadata:
                          finalPayload?.metadata || streamedMetadata || {},
                        streaming: false,
                      }
                    : msg
                )
              );
            }

            if (parsed.type === "error") {
              throw new Error(parsed.message || "Streaming failed");
            }
          }
        }
      }

      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === assistantIndex
            ? {
                ...msg,
                content: sanitizeAssistantContent(msg.content),
                metadata: finalPayload?.metadata || msg.metadata || {},
                streaming: false,
              }
            : msg
        )
      );
    } catch (err) {
      setError(err.message || "Failed to send message");

      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === assistantIndex
            ? {
                ...msg,
                content:
                  msg.content ||
                  "Sorry, something went wrong while streaming the response.",
                streaming: false,
              }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  }

  function handleComposerSubmit(e) {
    e.preventDefault();
    handleSendMessage();
  }

  function handleComposerKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function handleLogout() {
    setToken("");
    setUserId("");
    setMessages([]);
    setDocuments([]);
    setMessage("");
    setError("");
    setUploadSuccess("");
    setAuthSuccess("");
    setAge("");
    setGender("");
    setName("");
    setAuthName("");
    setAuthEmail("");
    setAuthPassword("");

    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
  }

  function clearChat() {
    setMessages([]);
    setError("");
  }

  const displayName = authName || name || "Patient";
  const uploadedCount = documents.length;

  if (!token) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <div className="brand auth-brand">
            <div className="logo-mark" aria-hidden="true"></div>
            <div>
              <h1>Medical AI</h1>
              <p>Secure medical assistant</p>
            </div>
          </div>

          <h2>{authMode === "signup" ? "Create account" : "Login"}</h2>

          <form onSubmit={handleAuthSubmit} className="stack">
            {authMode === "signup" ? (
              <input
                placeholder="Full name"
                value={authName}
                onChange={(e) => setAuthName(e.target.value)}
              />
            ) : null}

            <input
              type="email"
              placeholder="Email"
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
            />

            <button type="submit" disabled={authLoading}>
              {authLoading
                ? authMode === "signup"
                  ? "Creating..."
                  : "Logging in..."
                : authMode === "signup"
                ? "Sign up"
                : "Login"}
            </button>
          </form>

          <p className="meta">
            {authMode === "signup"
              ? "Already have an account?"
              : "Need an account?"}{" "}
            <button
              type="button"
              className="link-button"
              onClick={() =>
                setAuthMode((prev) => (prev === "login" ? "signup" : "login"))
              }
            >
              {authMode === "signup" ? "Login" : "Sign up"}
            </button>
          </p>

          {authSuccess ? <p className="success-text">{authSuccess}</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt"
        onChange={handleUpload}
        style={{ display: "none" }}
      />

      <aside className="sidebar">
        <div className="brand">
          <div className="logo-mark" aria-hidden="true"></div>
          <div>
            <h1>Medical AI</h1>
            <p>Secure medical assistant</p>
          </div>
        </div>

        <div className="panel stack">
          <span className="eyebrow">Profile</span>
          <h3>{displayName}</h3>
          <p className="meta">{authEmail || "Signed-in user"}</p>
          <p className="meta">
            {userId ? `Patient ID: ${userId}` : "Profile setup in progress"}
          </p>
        </div>

        <div className="panel stack">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "12px",
            }}
          >
            <span className="eyebrow">Documents</span>
            <button
              type="button"
              className="link-button"
              onClick={openFilePicker}
              disabled={uploading}
            >
              {uploading ? "Uploading..." : "Upload"}
            </button>
          </div>

          <div className="counter" tabIndex={0}>
            {uploadedCount} document{uploadedCount === 1 ? "" : "s"} connected
          </div>

          <div className="doc-list">
            {documents.length === 0 ? (
              <div className="doc-item">
                <span>No documents uploaded yet.</span>
              </div>
            ) : (
              documents.map((doc, idx) => (
                <div key={idx} className="doc-item">
                  <strong style={{ color: "var(--text-h)" }}>
                    {doc.filename || doc.name || `Document ${idx + 1}`}
                  </strong>
                  <span>{doc.type || doc.category || "Medical file"}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="panel stack">
          <span className="eyebrow">Care snapshot</span>
          <p className="meta">
            Ask about symptoms, medicines, lab reports, prescriptions, and
            uploaded files in one place.
          </p>
        </div>

        <div className="stack">
          <button
            type="button"
            className="secondary-button"
            onClick={clearChat}
          >
            Clear conversation
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </aside>

      <section className="main-panel">
        <header className="chat-header">
          <div>
            <div className="eyebrow">Assistant workspace</div>
            <h2>Consultation chat</h2>
            <p className="meta">
              {uploadedCount > 0
                ? `${uploadedCount} document(s) ready for context-aware answers`
                : "Upload a report or prescription to start a richer consultation"}
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={openFilePicker}
            disabled={uploading}
          >
            {uploading ? "Uploading..." : "Upload document"}
          </button>
        </header>

        <section className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="eyebrow">Ready</div>
              <h3 style={{ marginTop: "8px", marginBottom: "8px" }}>
                No messages yet
              </h3>
              <p>
                Upload a document and ask about symptoms, medicines,
                prescriptions, diagnoses, or next steps.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => {
              const urgency = msg?.metadata?.urgency || null;
              const badge = urgency ? urgencyConfig[urgency] : null;

              return (
                <article key={idx} className={`message ${msg.role}`}>
                  <div className="bubble">
                    {msg.role === "assistant" && badge ? (
                      <div className={badge.className}>{badge.label}</div>
                    ) : null}

                    {msg.role === "assistant" && msg.streaming ? (
                      <div className="eyebrow" style={{ marginBottom: "8px" }}>
                        Thinking...
                      </div>
                    ) : null}

                    {msg.role === "assistant" ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      <p>{msg.content}</p>
                    )}
                  </div>
                </article>
              );
            })
          )}

          <div ref={messagesEndRef} />
        </section>

        <form
          className="composer composer-inline"
          onSubmit={handleComposerSubmit}
        >
          <textarea
            rows="1"
            placeholder="Type your medical question..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleComposerKeyDown}
            disabled={loading}
          />

          <button
            type="button"
            className="icon-button"
            onClick={openFilePicker}
            title="Upload document"
            disabled={uploading}
          >
            {uploading ? "..." : "📎"}
          </button>

          <button type="submit" disabled={loading}>
            {loading ? "Streaming..." : "Send"}
          </button>
        </form>

        <div className="composer-status">
          {uploadSuccess ? <p className="success-text">{uploadSuccess}</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </section>
    </div>
  );
}
