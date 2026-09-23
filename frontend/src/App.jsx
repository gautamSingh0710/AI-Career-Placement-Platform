import { useState, useEffect, useRef } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

// =========================================================
// Small helper: animates a numeric stat from 0 -> value
// whenever value changes. Falls back to plain text for
// non-numeric values like "-".
// =========================================================
function useCountUp(value, duration = 700) {
  const [display, setDisplay] = useState(value);
  const frame = useRef(null);

  useEffect(() => {
    const numeric = parseFloat(value);
    if (Number.isNaN(numeric)) {
      setDisplay(value);
      return;
    }

    const start = performance.now();
    const from = 0;
    const isInt = Number.isInteger(numeric);

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = from + (numeric - from) * eased;
      setDisplay(isInt ? Math.round(current) : current.toFixed(1));
      if (progress < 1) frame.current = requestAnimationFrame(tick);
    }

    frame.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return display;
}

function App() {
  // =========================================================
  // AUTHENTICATION STATE
  // =========================================================
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [user, setUser] = useState({ name: "", email: "" });
  const [authForm, setAuthForm] = useState({ name: "", email: "", password: "" });

  // =========================================================
  // APP NAVIGATION & PROFILE STATE
  // =========================================================
  const [activePage, setActivePage] = useState("Dashboard");
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // Resume State
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [resumeUploading, setResumeUploading] = useState(false);

  // Dashboard Data
  const [dashboardData, setDashboardData] = useState({
    cgpa: "-",
    resumeScore: "-",
    eligibleCompanies: "-",
    backlogs: "-",
  });

  // Feature Results & Loaders
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello. I can help with your placement profile, eligibility, resume analysis, JD matching and skill gaps.",
    },
  ]);
  const [message, setMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const [eligibilityResult, setEligibilityResult] = useState("");
  const [eligibilityLoading, setEligibilityLoading] = useState(false);

  const [resumeResult, setResumeResult] = useState("");
  const [resumeLoading, setResumeLoading] = useState(false);

  const [jdText, setJdText] = useState("");
  const [savedJD, setSavedJD] = useState("");
  const [jdResult, setJdResult] = useState("");
  const [jdLoading, setJdLoading] = useState(false);

  const [skillGapResult, setSkillGapResult] = useState("");
  const [skillGapLoading, setSkillGapLoading] = useState(false);

  const [companiesResult, setCompaniesResult] = useState("");
  const [companiesLoading, setCompaniesLoading] = useState(false);

  // Animated dashboard numbers
  const animatedCgpa = useCountUp(dashboardData.cgpa);
  const animatedResumeScore = useCountUp(dashboardData.resumeScore);

  // =========================================================
  // API HELPERS
  // =========================================================
  async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(options.headers || {}),
      },
    });

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error("Backend returned an invalid response.");
    }

    if (!response.ok || data.status === "ERROR") {
      throw new Error(data.detail || data.message || data.response || data.error || "Request failed.");
    }
    return data;
  }

  async function callChatBackend(userMessage) {
    if (!user.email) throw new Error("Please login first.");
    const data = await apiRequest("/chat", {
      method: "POST",
      body: JSON.stringify({ email: user.email, message: userMessage }),
    });
    return data.response;
  }

  async function loadUserProfile(email) {
    if (!email) return;
    setProfileLoading(true);
    try {
      const data = await apiRequest(`/profile?email=${encodeURIComponent(email)}`);
      const userProfile = data.profile || data;
      setProfile(userProfile);

      setDashboardData({
        cgpa: userProfile.cgpa ?? "-",
        resumeScore: userProfile.resume_score ?? userProfile.resumeScore ?? "-",
        eligibleCompanies: userProfile.eligible_companies ?? userProfile.eligibleCompanies ?? "-",
        backlogs: userProfile.active_backlogs ?? userProfile.backlogs ?? "-",
      });

      setResumeUploaded(Boolean(userProfile.resume_uploaded ?? userProfile.resumeUploaded ?? userProfile.resume));

      if (userProfile.name) {
        setUser((prev) => ({ ...prev, name: userProfile.name }));
      }
    } catch (error) {
      console.error("Profile loading error:", error);
    } finally {
      setProfileLoading(false);
    }
  }

  // =========================================================
  // AUTH HANDLERS
  // =========================================================
  function handleAuthChange(event) {
    const { name, value } = event.target;
    setAuthForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    const name = authForm.name.trim();
    const email = authForm.email.trim().toLowerCase();
    const password = authForm.password.trim();

    if (!email || !password) return alert("Email and password are required.");
    if (showSignup && !name) return alert("Please enter your full name.");

    setUser({ name: showSignup ? name : email.split("@")[0], email });
    setIsLoggedIn(true);
    setAuthForm({ name: "", email: "", password: "" });
    setActivePage("Dashboard");
    await loadUserProfile(email);
  }

  function logout() {
    setIsLoggedIn(false);
    setUser({ name: "", email: "" });
    setProfile(null);
    setDashboardData({ cgpa: "-", resumeScore: "-", eligibleCompanies: "-", backlogs: "-" });
    setResumeUploaded(false);
    setResumeFile(null);
    setActivePage("Dashboard");
    setMessages([
      {
        role: "assistant",
        text: "Hello. I can help with your placement profile, eligibility, resume analysis, JD matching and skill gaps.",
      },
    ]);
  }

  // =========================================================
  // RESUME HANDLERS
  // =========================================================
  function handleResumeChange(event) {
    const file = event.target.files?.[0];
    if (!file) return setResumeFile(null);

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(file.type)) {
      alert("Please upload a PDF or DOCX resume.");
      event.target.value = "";
      return setResumeFile(null);
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Resume size must be below 10 MB.");
      event.target.value = "";
      return setResumeFile(null);
    }
    setResumeFile(file);
  }

  async function uploadResume() {
    if (!user.email) return alert("Please login first.");
    if (!resumeFile) return alert("Please select a resume first.");

    setResumeUploading(true);
    try {
      const formData = new FormData();
      formData.append("email", user.email);
      formData.append("file", resumeFile);

      const data = await apiRequest("/resume/upload", { method: "POST", body: formData });
      setResumeUploaded(true);
      if (data.profile) setProfile(data.profile);

      await loadUserProfile(user.email);
      setResumeFile(null);
      alert("Resume uploaded successfully.");
      setActivePage("Dashboard");
    } catch (error) {
      alert(`Resume upload failed: ${error.message}`);
    } finally {
      setResumeUploading(false);
    }
  }

  // =========================================================
  // ACTIONS / QUERIES
  // =========================================================
  async function sendMessage() {
    if (!message.trim() || chatLoading) return;
    const userMessage = message.trim();

    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setMessage("");
    setChatLoading(true);

    try {
      const result = await callChatBackend(userMessage);
      setMessages((prev) => [...prev, { role: "assistant", text: result }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", text: `Error: ${error.message}` }]);
    } finally {
      setChatLoading(false);
    }
  }

  async function openEligibility() {
    setActivePage("Eligibility");
    setEligibilityLoading(true);
    setEligibilityResult("");
    try {
      const result = await callChatBackend("Check my placement eligibility using my own profile and current placement criteria.");
      setEligibilityResult(result);
    } catch (error) {
      setEligibilityResult(`Error: ${error.message}`);
    } finally {
      setEligibilityLoading(false);
    }
  }

  async function openResumeAnalysis() {
    setActivePage("Resume Analysis");
    setResumeLoading(true);
    setResumeResult("");
    try {
      if (!resumeUploaded) {
        setResumeResult("Please upload your resume first.");
        return;
      }

      const data = await apiRequest("/resume/analyze", {
        method: "POST",
        body: JSON.stringify({ email: user.email }),
      });

      const score = data.resume_score ?? "-";
      setResumeResult(
        data.response || `Resume analysis complete. Your current score is ${score}/100.`
      );
      await loadUserProfile(user.email);
    } catch (error) {
      setResumeResult(`Error: ${error.message}`);
    } finally {
      setResumeLoading(false);
    }
  }

  function openJDPage(pageName) {
    setActivePage(pageName);
    if (savedJD && !jdText.trim()) setJdText(savedJD);
  }

  async function executeJDAction(prompt, setResult, setLoadingState) {
    if (!jdText.trim()) return;
    const currentJD = jdText.trim();
    setLoadingState(true);
    setResult("");
    try {
      const res = await callChatBackend(`${prompt}\n\n${currentJD}`);
      setSavedJD(currentJD);
      setResult(res);
    } catch (error) {
      setResult(`Error: ${error.message}`);
    } finally {
      setLoadingState(false);
    }
  }

  async function openCompanies() {
    setActivePage("Companies");
    setCompaniesLoading(true);
    setCompaniesResult("");
    try {
      const result = await callChatBackend("Show the companies I am eligible for using only my own profile and current placement criteria.");
      setCompaniesResult(result);
      await loadUserProfile(user.email);
    } catch (error) {
      setCompaniesResult(`Error: ${error.message}`);
    } finally {
      setCompaniesLoading(false);
    }
  }

  // =========================================================
  // UTILS
  // =========================================================
  function makeLinksClickable(text) {
    if (!text) return "";
    const combinedRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<]+)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = combinedRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      const isMarkdown = Boolean(match[1]);
      const label = isMarkdown ? match[1] : match[3].replace(/[),.;]+$/, "");
      const url = (isMarkdown ? match[2] : match[3]).replace(/[),.;]+$/, "");

      parts.push(
        <a key={match.index} href={url} target="_blank" rel="noopener noreferrer" className="resource-link">
          {label}
        </a>
      );
      lastIndex = combinedRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    return parts;
  }

  // =========================================================
  // AUTH VIEW
  // =========================================================
  if (!isLoggedIn) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-brand">
            <div className="brand-icon">AI</div>
            <div>
              <h1>CareerAI</h1>
              <span>Placement Platform</span>
            </div>
          </div>
          <h2>{showSignup ? "Create your account" : "Welcome back"}</h2>
          <p className="auth-subtitle">
            {showSignup ? "Create your placement profile" : "Login to access your placement dashboard"}
          </p>
          <form onSubmit={handleAuthSubmit}>
            {showSignup && (
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  name="name"
                  value={authForm.name}
                  onChange={handleAuthChange}
                  placeholder="Enter your full name"
                />
              </div>
            )}
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={authForm.email}
                onChange={handleAuthChange}
                placeholder="Enter your email"
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                name="password"
                value={authForm.password}
                onChange={handleAuthChange}
                placeholder="Enter your password"
              />
            </div>
            <button type="submit" className="auth-button">
              {showSignup ? "Create Account" : "Login"}
            </button>
          </form>
          <div className="auth-switch">
            {showSignup ? "Already have an account?" : "Don't have an account?"}
            <button type="button" onClick={() => setShowSignup((prev) => !prev)}>
              {showSignup ? "Login" : "Create Account"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================
  // DASHBOARD VIEW
  // =========================================================
  const navItems = [
    { name: "Dashboard", onClick: () => { setActivePage("Dashboard"); loadUserProfile(user.email); } },
    { name: "Resume Analysis", onClick: openResumeAnalysis },
    { name: "Eligibility", onClick: openEligibility },
    { name: "JD Matching", onClick: () => openJDPage("JD Matching") },
    { name: "Skill Gaps", onClick: () => openJDPage("Skill Gaps") },
    { name: "Companies", onClick: openCompanies },
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">AI</div>
          <div>
            <h2>CareerAI</h2>
            <span>Placement Platform</span>
          </div>
        </div>
        <nav>
          {navItems.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${activePage === item.name ? "active" : ""}`}
              onClick={item.onClick}
            >
              {item.name}
            </button>
          ))}
        </nav>
        <div className="profile-card">
          <div className="avatar">
            {user.name
              ? user.name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()
              : "U"}
          </div>
          <div className="profile-info">
            <strong>{user.name || "User"}</strong>
            <span>{user.email}</span>
          </div>
          <button className="logout-button" onClick={logout}>Logout</button>
        </div>
      </aside>

      {/* key={activePage} re-triggers the .main entrance animation on every page switch */}
      <main className="main" key={activePage}>
        <header className="topbar">
          <div>
            <h1>AI Career Placement Platform</h1>
            <p>Welcome, {user.name || "User"}</p>
          </div>
          <div className="status">
            <span></span> Agent Online
          </div>
        </header>

        {activePage === "Dashboard" && (
          <>
            <section className="dashboard-cards">
              <div className="card">
                <span>CGPA</span>
                <strong>{profileLoading ? "-" : animatedCgpa}</strong>
                <small>Your academic profile</small>
              </div>
              <div className="card">
                <span>Resume Score</span>
                <strong>{profileLoading ? "-" : animatedResumeScore}</strong>
                <small>Based on your uploaded resume</small>
              </div>
            </section>

            <section className="chat-container">
              <div className="chat-header">
                <h2>Your Resume</h2>
                <p>Upload your resume. It will be linked to your logged-in account.</p>
              </div>
              <div className="jd-input-container">
                <input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleResumeChange}
                />
                {resumeFile && <p>Selected: {resumeFile.name}</p>}
                {resumeUploaded && !resumeFile && <p>Your resume is already uploaded.</p>}
                <div className="page-actions">
                  <button
                    className="primary-button"
                    onClick={uploadResume}
                    disabled={resumeUploading || !resumeFile}
                  >
                    {resumeUploading ? "Uploading..." : "Upload Resume"}
                  </button>
                  <button
                    className="primary-button"
                    onClick={openResumeAnalysis}
                    disabled={resumeLoading || !resumeUploaded}
                  >
                    Analyze My Resume
                  </button>
                </div>
              </div>
            </section>

            <section className="chat-container">
              <div className="chat-header">
                <div>
                  <h2>Placement Assistant</h2>
                  <p>Ask about your eligibility, resume, companies, JD matching or skill gaps.</p>
                </div>
              </div>
              <div className="messages">
                {messages.map((item, index) => (
                  <div key={index} className={`message-row ${item.role}`}>
                    <div className="message">{makeLinksClickable(item.text)}</div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="message-row assistant">
                    <div className="message loading">Agent is thinking...</div>
                  </div>
                )}
              </div>
              <div className="suggestions">
                <button onClick={openEligibility}>Check eligibility</button>
                <button onClick={openResumeAnalysis}>Analyze resume</button>
                <button onClick={() => openJDPage("Skill Gaps")}>Show skill gaps</button>
                <button onClick={() => openJDPage("JD Matching")}>Match JD</button>
              </div>
              <div className="input-area">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder="Ask your placement assistant..."
                  rows="2"
                />
                <button
                  className="send-button"
                  onClick={sendMessage}
                  disabled={chatLoading || !message.trim()}
                >
                  Send
                </button>
              </div>
            </section>
          </>
        )}

        {activePage === "Eligibility" && (
          <section className="chat-container">
            <div className="chat-header">
              <h2>Placement Eligibility</h2>
              <p>Checking your profile against the current placement criteria.</p>
            </div>
            <div className="messages">
              <div className="message-row assistant">
                <div className={`message ${eligibilityLoading ? "loading" : "result-message"}`}>
                  {eligibilityLoading ? "Checking your eligibility..." : makeLinksClickable(eligibilityResult || "Click Check Eligibility to get your current result.")}
                </div>
              </div>
            </div>
          </section>
        )}

        {activePage === "Resume Analysis" && (
          <section className="chat-container">
            <div className="chat-header">
              <h2>Resume Analysis</h2>
              <p>Analyze your own uploaded resume.</p>
            </div>
            <div className="messages">
              <div className="message-row assistant">
                <div className={`message ${resumeLoading ? "loading" : "result-message"}`}>
                  {resumeLoading
                    ? "Analyzing your resume..."
                    : makeLinksClickable(
                        resumeResult || (resumeUploaded ? "Click Analyze Resume below." : "Please upload your resume first.")
                      )}
                </div>
              </div>
            </div>
            <div className="page-actions">
              <button
                className="primary-button"
                onClick={openResumeAnalysis}
                disabled={resumeLoading || !resumeUploaded}
              >
                {resumeLoading ? "Analyzing..." : "Analyze Resume"}
              </button>
            </div>
          </section>
        )}

        {activePage === "JD Matching" && (
          <section className="chat-container">
            <div className="chat-header">
              <h2>JD Matching</h2>
              <p>Paste a Job Description and analyze or match it with your own resume.</p>
            </div>
            <div className="jd-input-container">
              <textarea
                className="jd-textarea"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste Job Description here..."
                rows="12"
              />
              <div className="page-actions">
                <button
                  className="primary-button"
                  onClick={() => executeJDAction("Analyze this Job Description for me:", setJdResult, setJdLoading)}
                  disabled={jdLoading || !jdText.trim()}
                >
                  {jdLoading ? "Processing..." : "Analyze JD"}
                </button>
                <button
                  className="primary-button"
                  onClick={() => {
                    if (!resumeUploaded) return setJdResult("Please upload your resume first.");
                    executeJDAction("Match my uploaded resume with this Job Description. Use only my own resume and profile data.", setJdResult, setJdLoading);
                  }}
                  disabled={jdLoading || !jdText.trim() || !resumeUploaded}
                >
                  {jdLoading ? "Processing..." : "Match My Resume"}
                </button>
              </div>
            </div>
            <div className="messages">
              {jdResult && (
                <div className="message-row assistant">
                  <div className="message result-message">{makeLinksClickable(jdResult)}</div>
                </div>
              )}
            </div>
          </section>
        )}

        {activePage === "Skill Gaps" && (
          <section className="chat-container">
            <div className="chat-header">
              <h2>Skill Gap Analysis</h2>
              <p>Find the skills missing for your target JD based on your own resume.</p>
            </div>
            <div className="jd-input-container">
              <textarea
                className="jd-textarea"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder={savedJD ? "JD loaded from JD Matching." : "Paste the Job Description here..."}
                rows="12"
              />
              <div className="page-actions">
                <button
                  className="primary-button"
                  onClick={() => {
                    if (!resumeUploaded) return setSkillGapResult("Please upload your resume first.");
                    executeJDAction("Show my skill gaps for this JD using only my uploaded resume and my profile:", setSkillGapResult, setSkillGapLoading);
                  }}
                  disabled={skillGapLoading || !resumeUploaded || (!jdText.trim() && !savedJD)}
                >
                  {skillGapLoading ? "Analyzing..." : "Show Skill Gaps"}
                </button>
              </div>
            </div>
            <div className="messages">
              {(skillGapLoading || skillGapResult) && (
                <div className="message-row assistant">
                  <div className={`message ${skillGapLoading ? "loading" : "result-message"}`}>
                    {skillGapLoading ? "Analyzing your skill gaps..." : makeLinksClickable(skillGapResult)}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {activePage === "Companies" && (
          <section className="chat-container">
            <div className="chat-header">
              <h2>Eligible Companies</h2>
              <p>Companies based on your own profile and current placement criteria.</p>
            </div>
            <div className="messages">
              <div className="message-row assistant">
                <div className={`message ${companiesLoading ? "loading" : "result-message"}`}>
                  {companiesLoading ? "Finding your eligible companies..." : makeLinksClickable(companiesResult || "Click Refresh Companies below.")}
                </div>
              </div>
            </div>
            <div className="page-actions">
              <button className="primary-button" onClick={openCompanies} disabled={companiesLoading}>
                {companiesLoading ? "Loading..." : "Refresh Companies"}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
