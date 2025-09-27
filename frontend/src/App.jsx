import { useState } from "react";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    try {
      setError("");
      const res = await fetch("http://localhost/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) throw new Error("Login failed");

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      alert("Login success! Token saved to localStorage");
    } catch (err) {
      setError(err.message);
    }
  };

  const handleGetProfile = async () => {
    try {
      setError("");
      const token = localStorage.getItem("token");
      if (!token) throw new Error("No token found, please login first");

      const res = await fetch("http://localhost/profile/request-profile", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Failed to fetch profile");

      const data = await res.json();
      setProfile(data);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Auth Demo</h1>

      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ marginRight: "0.5rem" }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ marginRight: "0.5rem" }}
        />
        <button onClick={handleLogin}>Login</button>
      </div>

      <button onClick={handleGetProfile}>Get Profile</button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {profile && (
        <pre style={{ textAlign: "left", marginTop: "1rem" }}>
          {JSON.stringify(profile, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;