import { GoogleLogin } from "@react-oauth/google";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { signInWithGoogle } from "../api/auth.ts";
import { useAuth } from "../context/AuthContext.tsx";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  async function handleSuccess(credential: string) {
    try {
      const res = await signInWithGoogle(credential);
      login(res.access_token, res.user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      alert(`Sign-in failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50">
      <div className="bg-white rounded-2xl shadow-sm border border-neutral-200 px-10 py-12 w-full max-w-sm text-center">
        <div className="text-5xl mb-4">🛡️</div>
        <h1 className="text-2xl font-semibold text-neutral-900 mb-1">code-scanner</h1>
        <p className="text-sm text-neutral-500 mb-8">
          AI-powered security analysis for your code
        </p>
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={(res) => {
              if (res.credential) handleSuccess(res.credential);
            }}
            onError={() => alert("Google sign-in failed")}
            theme="outline"
            shape="rectangular"
            text="signin_with"
            width="260"
          />
        </div>
        <p className="mt-6 text-xs text-neutral-400">
          Sign in to view your scans and manage the knowledge base.
        </p>
      </div>
    </div>
  );
}
