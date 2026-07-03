import ReactMarkdown from "react-markdown";
import { useEffect, useRef, useState } from "react";
import {
  createUser,
  listDocuments,
  login,
  sendMessage,
  signup,
  uploadDocument,
} from "./services/api";
import "./styles.css";

export default function App() {
  const fileInputRef = useRef(null);

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
      setError(err.message);
    }
  }

  async function refreshDocuments(currentUserId = userId) {
    if (!currentUserId || !token) return;

    try {
      const data = await listDocuments(currentUserId, token);
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    if (token && userId) {
      refreshDocuments(userId);
    }
  }, [token, userId]);

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
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setMessage("");
    setLoading(true);
    setError("");

    try {
      const data = await sendMessage(
        {
          user_id: Number(userId),
          message: userText,
        },
        token
      );

      console.log("chat response data:", data);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data.response ||
            data.message ||
            data.assistant_message ||
            data.reply ||
            JSON.stringify(data),
        },
      ]);
    } catch (err) {
      setError(err.message || "Failed to send message");
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

  useEffect(() => {
    if (token && !userId) {
      handleCreateUserProfile();
    }
  }, [token]);

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
    <div className="chat-screen">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt"
        onChange={handleUpload}
        style={{ display: "none" }}
      />

      <header className="chat-header">
        <div className="brand">
          <div className="logo-mark" aria-hidden="true"></div>
          <div>
            <h1>Medical AI</h1>
            <p>
              {documents.length > 0
                ? `${documents.length} document(s) uploaded`
                : "No documents uploaded yet"}
            </p>
          </div>
        </div>

        <button type="button" className="secondary-button" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <main className="chat-main">
        <section className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>No messages yet</h3>
              <p>Upload a document and ask about symptoms, medicines, or prescriptions.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <article key={idx} className={`message ${msg.role}`}>
                <div className="bubble">
                  {msg.role === "assistant" ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </article>
            ))
          )}

          {loading ? (
            <article className="message assistant">
              <div className="bubble">Thinking...</div>
            </article>
          ) : null}
        </section>

        <form className="composer composer-inline" onSubmit={handleComposerSubmit}>
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
            Send
          </button>
        </form>

        {uploadSuccess ? <p className="success-text composer-status">{uploadSuccess}</p> : null}
        {error ? <p className="error-text composer-status">{error}</p> : null}
      </main>
    </div>
  );
}