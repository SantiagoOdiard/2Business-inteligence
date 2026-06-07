import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LockKeyhole } from "lucide-react";
import { login } from "../api/client";
import { SavingState } from "../components/State";

export function Login() {
  const [username, setUsername] = useState("admin@enterprise-ops.com");
  const [password, setPassword] = useState("Enterprise123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Credentials were rejected or the API is unavailable.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-canvas px-4">
      <form onSubmit={submit} className="w-full max-w-md rounded-md border border-line bg-white p-6 shadow-panel">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-teal-50 text-primary">
            <LockKeyhole className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Enterprise Operations Intelligence Suite</h1>
            <p className="text-sm text-slate-500">Secure access with role-based permissions.</p>
          </div>
        </div>
        <label className="mb-3 block text-sm font-medium">
          Email
          <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label className="mb-4 block text-sm font-medium">
          Password
          <input className="mt-1 w-full rounded-md border border-line px-3 py-2" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {error && <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <button className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 font-medium text-white" disabled={busy}>
          {busy && <SavingState />}
          Login
        </button>
      </form>
    </main>
  );
}
