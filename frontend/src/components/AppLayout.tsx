import { NavLink, Outlet } from "react-router-dom";

const navigationItems = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Accounts", path: "/accounts" },
  { label: "Transactions", path: "/transactions" },
  { label: "Budgets", path: "/budgets" },
  { label: "Transfers", path: "/transfers" },
  { label: "CSV Import / Export", path: "/csv" },
];

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-[#080b16]">
      {/* Shared application navigation */}
      <header className="sticky top-0 z-50 border-b border-gray-800 bg-[#080b16]/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-8">

          {/* Brand */}
          <NavLink
            to="/dashboard"
            className="flex shrink-0 items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-xl font-bold text-cyan-400">
              S
            </div>

            <div>
              <p className="text-lg font-bold tracking-tight text-white">
                SpendWise <span className="text-cyan-400">AI</span>
              </p>
              <p className="text-xs text-gray-500">
                Personal Finance Manager
              </p>
            </div>
          </NavLink>

          {/* Responsive navigation links */}
          <nav
            aria-label="Main navigation"
            className="flex gap-2 overflow-x-auto pb-1 lg:pb-0"
          >
            {navigationItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/dashboard"}
                className={({ isActive }) =>
                  `shrink-0 rounded-lg px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? "bg-cyan-500/10 text-cyan-400"
                      : "text-gray-400 hover:bg-gray-800 hover:text-white"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      {/* Render the currently selected protected page */}
      <div>
        <Outlet />
      </div>
    </div>
  );
}