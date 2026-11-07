import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { accountApi } from "../features/accounts/AccountApi";
import { categoryApi } from "../features/categories/CategoryApi";
import { transactionApi } from "../features/transactions/TransactionApi";
import type { TransactionType } from "../features/transactions/TransactionTypes";

export default function Transactions() {
  const queryClient = useQueryClient();

  const [type, setType] = useState<TransactionType>("expense");
  const [accountId, setAccountId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [merchant, setMerchant] = useState("");
  const [date, setDate] = useState(
    new Date().toLocaleDateString("en-CA")
  );
  const [error, setError] = useState("");

  // The selected account determines where this transaction is recorded and its currency.
  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: accountApi.getAll,
  });

  // Load categories matching the selected transaction type (income or expense).
  const categories = useQuery({
    queryKey: ["categories", type],
    queryFn: () => categoryApi.getAll(type),
  });

  // Display the latest 50 records; filtering and pagination can be added separately.
  const transactions = useQuery({
    queryKey: ["transactions"],
    queryFn: () => transactionApi.getAll({ limit: 50, offset: 0 }),
  });

  // Refresh transactions, dashboard metrics, and account balances after a successful write.
  const createTransaction = useMutation({
    mutationFn: transactionApi.create,
    onSuccess: async () => {
      setAmount("");
      setDescription("");
      setMerchant("");
      setCategoryId("");
      setError("");

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["accounts"] }),
      ]);
    },
    onError: () => setError("Could not create transaction. Check your account and category."),
  });

  // Validate the selected account and build the request using the backend schema.
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    const account = accounts.data?.find((item) => item.id === accountId);

    if (!account) {
      setError("Please select an account.");
      return;
    }

    createTransaction.mutate({
      account_id: account.id,
      category_id: categoryId || null,
      type,
      amount: Number(amount),
      currency: account.currency,
      description,
      merchant: merchant || null,
      transaction_date: date,
      notes: null,
    });
  };

  return (
    <main className="min-h-screen bg-[#080b16] p-6 text-white md:p-10">
      <h1 className="mb-8 text-3xl font-bold">Transactions</h1>

      <form
        onSubmit={handleSubmit}
        className="mb-10 grid gap-4 rounded-xl border border-gray-800 bg-[#111827] p-6 md:grid-cols-2"
      >
        <select
          value={type}
          onChange={(e) => {
            setType(e.target.value as TransactionType);
            setCategoryId("");
          }}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        >
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>

        <select
          required
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        >
          <option value="">Select account</option>
          {accounts.data?.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.currency})
            </option>
          ))}
        </select>

        <select
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        >
          <option value="">Uncategorized</option>
          {categories.data?.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>

        <input
          type="number"
          required
          min="0.0001"
          step="0.0001"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <input
          required
          minLength={2}
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <input
          placeholder="Merchant (optional)"
          value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <input
          type="date"
          required
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <button
          disabled={createTransaction.isPending || !accounts.data?.length}
          className="rounded-lg bg-cyan-500 p-3 font-semibold text-black disabled:opacity-50"
        >
          {createTransaction.isPending ? "Saving..." : "Add Transaction"}
        </button>

        {error && <p role="alert" className="text-red-400 md:col-span-2">{error}</p>}
      </form>

      <section className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <h2 className="mb-5 text-xl font-semibold">All Transactions</h2>

        {transactions.isLoading ? (
          <p>Loading transactions...</p>
        ) : transactions.isError ? (
          <p className="text-red-400">Unable to load transactions.</p>
        ) : transactions.data?.items.length === 0 ? (
          <p className="text-gray-400">No transactions found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-gray-400">
                <tr>
                  <th className="p-3">Description</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Date</th>
                  <th className="p-3">Amount</th>
                </tr>
              </thead>
              <tbody>
                {transactions.data?.items.map((transaction) => (
                  <tr key={transaction.id} className="border-t border-gray-800">
                    <td className="p-3">{transaction.description}</td>
                    <td className="p-3 capitalize">{transaction.type}</td>
                    <td className="p-3">{transaction.transaction_date}</td>
                    <td className="p-3">
                      {transaction.currency} {Number(transaction.amount).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}