export default function Dashboard() {
  return (
    <main className="min-h-screen bg-[#080b16] p-8 text-white">
      <h1 className="text-3xl font-bold">SpendWise AI</h1>
      <p className="mt-2 text-gray-400">
        Your personal finance dashboard.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {["Total Balance", "Income", "Expenses"].map((item) => (
          <div
            key={item}
            className="rounded-xl border border-gray-800 bg-[#111827] p-6"
          >
            <p className="text-sm text-gray-400">{item}</p>
            <p className="mt-3 text-2xl font-semibold">₹0.00</p>
          </div>
        ))}
      </div>
    </main>
  );
}