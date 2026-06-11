import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.tsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <aside className="w-60 min-h-screen bg-neutral-900 text-white flex flex-col">
      <div className="px-6 py-5 border-b border-neutral-700">
        <span className="text-lg font-semibold tracking-tight">🛡 code-scanner</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              isActive
                ? "bg-blue-600 text-white"
                : "text-neutral-400 hover:bg-neutral-800 hover:text-white"
            }`
          }
        >
          <span>📋</span> Scans
        </NavLink>
        <NavLink
          to="/knowledge"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              isActive
                ? "bg-blue-600 text-white"
                : "text-neutral-400 hover:bg-neutral-800 hover:text-white"
            }`
          }
        >
          <span>📚</span> Knowledge Base
        </NavLink>
      </nav>

      {user && (
        <div className="px-4 py-4 border-t border-neutral-700">
          <div className="flex items-center gap-3 mb-3">
            {user.picture ? (
              <img src={user.picture} alt="" className="w-8 h-8 rounded-full" />
            ) : (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-semibold">
                {user.name[0]}
              </div>
            )}
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.name}</p>
              <p className="text-xs text-neutral-400 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left text-xs text-neutral-400 hover:text-white transition-colors px-1"
          >
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
