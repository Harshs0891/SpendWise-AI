import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { accountApi } from "../features/accounts/AccountApi";
import type { AccountType } from "../features/accounts/AccountTypes";

export default function Accounts() {
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [accountType, setAccountType] = useState<AccountType>("bank");
  const [openingBalance, setOpeningBalance] = useState("0");
  const [error, setError] = useState("");

  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: accountApi.getAll,
  });

  const createAccount = useMutation({
    mutationFn: accountApi.create,
    onSuccess: async () => {
      setName("");
      setOpeningBalance("0");
      setError("");
      await queryClient.invalidateQueries({ queryKey: ["accounts"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: () => setError("Could not create account."),
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    createAccount.mutate({
      name,
      account_type: accountType,
      currency: "INR",
      opening_balance: Number(openingBalance),
    });
  };

  return (
    <main className="min-h-screen bg-[#080b16] p-6 text-white md:p-10">
      <h1 className="mb-8 text-3xl font-bold">My Accounts</h1>

      <form
        onSubmit={handleSubmit}
        className="mb-8 grid gap-4 rounded-xl border border-gray-800 bg-[#111827] p-6 md:grid-cols-4"
      >
        <input
          required
          minLength={2}
          placeholder="Account name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <select
          value={accountType}
          onChange={(e) => setAccountType(e.target.value as AccountType)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        >
          <option value="bank">Bank</option>
          <option value="savings">Savings</option>
          <option value="cash">Cash</option>
          <option value="wallet">Wallet</option>
          <option value="credit_card">Credit Card</option>
        </select>

        <input
          type="number"
          min="0"
          step="0.0001"
          required
          value={openingBalance}
          onChange={(e) => setOpeningBalance(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
          placeholder="Opening balance"
        />

        <button
          disabled={createAccount.isPending}
          className="rounded-lg bg-cyan-500 p-3 font-semibold text-black disabled:opacity-50"
        >
          {createAccount.isPending ? "Creating..." : "Add Account"}
        </button>

        {error && <p role="alert" className="text-red-400">{error}</p>}
      </form>

      {accounts.isLoading ? (
        <p>Loading accounts...</p>
      ) : accounts.isError ? (
        <p className="text-red-400">Unable to load accounts.</p>
      ) : accounts.data?.length === 0 ? (
        <p className="text-gray-400">No accounts yet. Create your first account.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {accounts.data?.map((account) => (
            <div
              key={account.id}
              className="rounded-xl border border-gray-800 bg-[#111827] p-6"
            >
              <h2 className="text-xl font-semibold">{account.name}</h2>
              <p className="mt-2 text-sm text-gray-400">
                {account.account_type} · {account.currency}
              </p>
              <p className="mt-4 text-2xl font-bold">
                {new Intl.NumberFormat("en-IN", {
                  style: "currency",
                  currency: account.currency,
                }).format(Number(account.opening_balance))}
              </p>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}