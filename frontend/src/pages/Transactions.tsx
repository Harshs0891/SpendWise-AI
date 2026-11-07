import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { accountApi } from "../features/accounts/AccountApi";
import { categoryApi } from "../features/categories/CategoryApi";
import { transactionApi } from "../features/transactions/TransactionApi";

import type {
  TransactionFilters,
  TransactionType,
} from "../features/transactions/TransactionTypes";

// Keep pagination small enough for a readable transaction table.
const PAGE_SIZE = 10;

const inputClass =
  "w-full rounded-lg border border-gray-700 bg-[#080b16] px-3 py-3 text-sm text-white outline-none transition focus:border-cyan-500";

const formatMoney = (amount: number, currency: string) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(amount));

export default function Transactions() {
  const queryClient = useQueryClient();

  // New transaction form state.
  const [createType, setCreateType] = useState<TransactionType>("expense");
  const [accountId, setAccountId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [merchant, setMerchant] = useState("");
  const [date, setDate] = useState(
    new Date().toLocaleDateString("en-CA"),
  );
  const [formError, setFormError] = useState("");

  // Transaction filter state.
  const [filterType, setFilterType] = useState<
    "" | TransactionType
  >("");
  const [filterAccountId, setFilterAccountId] = useState("");
  const [filterCategoryId, setFilterCategoryId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Server-side pagination state.
  const [page, setPage] = useState(0);

  // Fetch active accounts for the form and filters.
  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: accountApi.getAll,
  });

  // Fetch categories according to the selected transaction type.
  const categories = useQuery({
    queryKey: ["categories", createType],
    queryFn: () => categoryApi.getAll(createType),
  });

  // Fetch categories available for the current filter.
  const filterCategories = useQuery({
    queryKey: ["categories", "transaction-filters", filterType],
    queryFn: () => categoryApi.getAll(filterType || undefined),
  });

  // Build the server-side filter and pagination parameters.
  const filters: TransactionFilters = {
    type: filterType || undefined,
    account_id: filterAccountId || undefined,
    category_id: filterCategoryId || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  };

  // React Query refetches whenever filters or page number changes.
  const transactions = useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => transactionApi.getAll(filters),
    placeholderData: (previousData) => previousData,
  });

  // Create a transaction and refresh the financial data.
  const createTransaction = useMutation({
    mutationFn: transactionApi.create,

    onSuccess: async () => {
      setAmount("");
      setDescription("");
      setMerchant("");
      setCategoryId("");
      setFormError("");

      // Return to the first page so the newest transaction is visible.
      setPage(0);

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["accounts"] }),
      ]);
    },

    onError: () => {
      setFormError(
        "Could not create transaction. Please check your account, category and input values.",
      );
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const account = accounts.data?.find(
      (item) => item.id === accountId,
    );

    if (!account) {
      setFormError("Please select a valid account.");
      return;
    }

    const numericAmount = Number(amount);

    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setFormError("Please enter a valid amount greater than zero.");
      return;
    }

    if (description.trim().length < 2) {
      setFormError("Description must contain at least 2 characters.");
      return;
    }

    createTransaction.mutate({
      account_id: account.id,
      category_id: categoryId || null,
      type: createType,
      amount: numericAmount,
      currency: account.currency,
      description: description.trim(),
      merchant: merchant.trim() || null,
      transaction_date: date,
      notes: null,
    });
  }

  // Reset all filters and return to the first page.
  function clearFilters() {
    setFilterType("");
    setFilterAccountId("");
    setFilterCategoryId("");
    setStartDate("");
    setEndDate("");
    setPage(0);
  }

  const total = transactions.data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentItems = transactions.data?.items ?? [];

  const hasActiveFilters = Boolean(
    filterType ||
    filterAccountId ||
    filterCategoryId ||
    startDate ||
    endDate,
  );

  return (
    <main className="min-h-screen space-y-8 bg-[#080b16] p-6 text-white md:p-10">

      {/* Page heading */}
      <header>
        <h1 className="text-3xl font-bold">Transactions</h1>
        <p className="mt-2 text-sm text-gray-400">
          Manage, track and analyze your income and expenses.
        </p>
      </header>

      {/* Add transaction form */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <h2 className="mb-5 text-xl font-semibold">
          Add Transaction
        </h2>

        <form
          onSubmit={handleSubmit}
          className="grid gap-4 md:grid-cols-2"
        >
          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Transaction type
            </label>

            <select
              value={createType}
              onChange={(event) => {
                setCreateType(event.target.value as TransactionType);
                setCategoryId("");
              }}
              className={inputClass}
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Account
            </label>

            <select
              required
              value={accountId}
              onChange={(event) => setAccountId(event.target.value)}
              className={inputClass}
            >
              <option value="">Select account</option>

              {accounts.data?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name} ({account.currency})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Category
            </label>

            <select
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
              className={inputClass}
            >
              <option value="">Uncategorized</option>

              {categories.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Amount
            </label>

            <input
              type="number"
              required
              min="0.0001"
              step="0.0001"
              placeholder="Enter amount"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Description
            </label>

            <input
              required
              minLength={2}
              maxLength={255}
              placeholder="Transaction description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Merchant (optional)
            </label>

            <input
              placeholder="Merchant name"
              value={merchant}
              onChange={(event) => setMerchant(event.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Transaction date
            </label>

            <input
              type="date"
              required
              value={date}
              onChange={(event) => setDate(event.target.value)}
              className={inputClass}
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={
                createTransaction.isPending ||
                !accounts.data?.length
              }
              className="w-full rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-black transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {createTransaction.isPending
                ? "Saving..."
                : "Add Transaction"}
            </button>
          </div>

          {formError && (
            <p role="alert" className="text-sm text-red-400 md:col-span-2">
              {formError}
            </p>
          )}
        </form>
      </section>

      {/* Transaction history and filters */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-6">

        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">
              All Transactions
            </h2>
            <p className="mt-1 text-sm text-gray-400">
              {total} matching transaction(s)
            </p>
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 transition hover:bg-gray-800"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Filter controls */}
        <div className="mb-6 grid gap-4 rounded-xl border border-gray-800 bg-[#080b16] p-4 sm:grid-cols-2 lg:grid-cols-3">

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-400">
              Transaction type
            </label>

            <select
              value={filterType}
              onChange={(event) => {
                setFilterType(event.target.value as "" | TransactionType);
                setFilterCategoryId("");
                setPage(0);
              }}
              className={inputClass}
            >
              <option value="">All types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-400">
              Account
            </label>

            <select
              value={filterAccountId}
              onChange={(event) => {
                setFilterAccountId(event.target.value);
                setPage(0);
              }}
              className={inputClass}
            >
              <option value="">All accounts</option>

              {accounts.data?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-400">
              Category
            </label>

            <select
              value={filterCategoryId}
              onChange={(event) => {
                setFilterCategoryId(event.target.value);
                setPage(0);
              }}
              className={inputClass}
            >
              <option value="">All categories</option>

              {filterCategories.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-400">
              Start date
            </label>

            <input
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) => {
                setStartDate(event.target.value);
                setPage(0);
              }}
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-400">
              End date
            </label>

            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              onChange={(event) => {
                setEndDate(event.target.value);
                setPage(0);
              }}
              className={inputClass}
            />
          </div>

        </div>

        {/* Transaction table */}
        {transactions.isLoading ? (
          <p className="py-10 text-center text-gray-400">
            Loading transactions...
          </p>
        ) : transactions.isError ? (
          <p className="py-10 text-center text-red-400">
            Unable to load transactions. Please try again.
          </p>
        ) : currentItems.length === 0 ? (
          <div className="py-12 text-center">
            <p className="font-medium text-gray-300">
              No transactions found
            </p>
            <p className="mt-2 text-sm text-gray-500">
              Try changing your filters or adding a transaction.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[650px] text-left text-sm">
                <thead className="border-b border-gray-700 text-xs uppercase tracking-wide text-gray-400">
                  <tr>
                    <th className="px-3 py-4">Description</th>
                    <th className="px-3 py-4">Type</th>
                    <th className="px-3 py-4">Category</th>
                    <th className="px-3 py-4">Date</th>
                    <th className="px-3 py-4 text-right">Amount</th>
                  </tr>
                </thead>

                <tbody>
                  {currentItems.map((transaction) => {
                    const account = accounts.data?.find(
                      (item) => item.id === transaction.account_id,
                    );

                    return (
                      <tr
                        key={transaction.id}
                        className="border-b border-gray-800 transition hover:bg-gray-800/40"
                      >
                        <td className="px-3 py-4">
                          <p className="font-medium text-gray-200">
                            {transaction.description}
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            {account?.name ?? "Account"}
                            {transaction.merchant
                              ? ` · ${transaction.merchant}`
                              : ""}
                          </p>
                        </td>

                        <td className="px-3 py-4">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                              transaction.type === "income"
                                ? "bg-green-500/10 text-green-400"
                                : "bg-red-500/10 text-red-400"
                            }`}
                          >
                            {transaction.type}
                          </span>
                        </td>

                        <td className="px-3 py-4 text-gray-400">
                          {transaction.category_id
                            ? filterCategories.data?.find(
                                (category) =>
                                  category.id === transaction.category_id,
                              )?.name ?? "Category"
                            : "Uncategorized"}
                        </td>

                        <td className="whitespace-nowrap px-3 py-4 text-gray-400">
                          {transaction.transaction_date}
                        </td>

                        <td
                          className={`whitespace-nowrap px-3 py-4 text-right font-semibold ${
                            transaction.type === "income"
                              ? "text-green-400"
                              : "text-red-400"
                          }`}
                        >
                          {transaction.type === "income" ? "+" : "-"}
                          {formatMoney(
                            transaction.amount,
                            transaction.currency,
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination controls */}
            <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-gray-800 pt-5">

              <p className="text-sm text-gray-400">
                Showing{" "}
                <span className="font-medium text-white">
                  {page * PAGE_SIZE + 1}
                </span>
                {" "}–{" "}
                <span className="font-medium text-white">
                  {page * PAGE_SIZE + currentItems.length}
                </span>
                {" "}of{" "}
                <span className="font-medium text-white">
                  {total}
                </span>
              </p>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  disabled={page === 0 || transactions.isFetching}
                  onClick={() => setPage((current) => current - 1)}
                  className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>

                <span className="text-sm text-gray-400">
                  Page {page + 1} of {Math.max(totalPages, 1)}
                </span>

                <button
                  type="button"
                  disabled={
                    page + 1 >= totalPages ||
                    transactions.isFetching
                  }
                  onClick={() => setPage((current) => current + 1)}
                  className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </main>
  );
}