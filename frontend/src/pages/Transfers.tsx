import { useMemo, useState, type FormEvent } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { transferApi } from "../features/transfers/TransferApi";
import type { TransferCreate } from "../features/transfers/TransferTypes";

import { accountApi } from "../features/accounts/AccountApi";
import type { Account } from "../features/accounts/AccountTypes";

// Shared styling for all form inputs.
const inputClass =
  "w-full rounded-xl border border-gray-700 bg-[#080b16] px-4 py-3 text-sm text-white outline-none transition placeholder:text-gray-500 hover:border-gray-600 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20";

// Format monetary values using the Indian numbering system.
function formatMoney(amount: number, currency: string) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(amount));
}

// Use local date rather than UTC to avoid timezone-related date shifts.
function getLocalDate() {
  const today = new Date();
  const offset = today.getTimezoneOffset();

  return new Date(today.getTime() - offset * 60_000)
    .toISOString()
    .slice(0, 10);
}

// Extract useful error messages from backend responses.
function getErrorMessage(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error
  ) {
    const response = (
      error as {
        response?: {
          data?: {
            detail?: string;
            message?: string;
          };
        };
      }
    ).response;

    return (
      response?.data?.detail ??
      response?.data?.message ??
      "Unable to complete the transfer. Please try again."
    );
  }

  return "Something went wrong. Please try again.";
}

export default function Transfers() {
  const queryClient = useQueryClient();

  // Transfer form state.
  const [sourceAccountId, setSourceAccountId] = useState("");
  const [destinationAccountId, setDestinationAccountId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [transactionDate, setTransactionDate] = useState(getLocalDate());

  // User feedback state.
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Fetch active accounts for the transfer form.
  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: accountApi.getAll,
  });

  // Fetch the latest transfer history.
  const transfersQuery = useQuery({
    queryKey: ["transfers"],
    queryFn: () => transferApi.getAll(20, 0),
  });

  const accounts: Account[] = useMemo(
    () => accountsQuery.data ?? [],
    [accountsQuery.data],
  );

  // Resolve the selected source account.
  const sourceAccount = useMemo(
    () => accounts.find((account) => account.id === sourceAccountId),
    [accounts, sourceAccountId],
  );

  // Resolve the selected destination account.
  const destinationAccount = useMemo(
    () => accounts.find((account) => account.id === destinationAccountId),
    [accounts, destinationAccountId],
  );

  // Create a transfer and refresh all affected financial information.
  const transferMutation = useMutation({
    mutationFn: (data: TransferCreate) => transferApi.create(data),

    onSuccess: async () => {
      setSuccessMessage("Transfer completed successfully!");
      setErrorMessage("");

      // Reset the form after a successful transfer.
      setAmount("");
      setDescription("");
      setSourceAccountId("");
      setDestinationAccountId("");
      setTransactionDate(getLocalDate());

      // A transfer creates two ledger entries and changes account balances.
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transfers"] }),
        queryClient.invalidateQueries({ queryKey: ["accounts"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
      ]);
    },

    onError: (error: unknown) => {
      setSuccessMessage("");
      setErrorMessage(getErrorMessage(error));
    },
  });

  // Validate all fields before submitting the transfer.
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setErrorMessage("");
    setSuccessMessage("");

    const numericAmount = Number(amount);

    if (!sourceAccountId || !destinationAccountId) {
      setErrorMessage(
        "Please select both source and destination accounts.",
      );
      return;
    }

    if (sourceAccountId === destinationAccountId) {
      setErrorMessage(
        "Source and destination accounts must be different.",
      );
      return;
    }

    if (
      !Number.isFinite(numericAmount) ||
      numericAmount <= 0
    ) {
      setErrorMessage("Enter a valid amount greater than zero.");
      return;
    }

    if (!sourceAccount || !destinationAccount) {
      setErrorMessage("Please select valid accounts.");
      return;
    }

    if (sourceAccount.currency !== destinationAccount.currency) {
      setErrorMessage(
        "Transfers between different currencies are not supported.",
      );
      return;
    }

    if (description.trim().length < 2) {
      setErrorMessage(
        "Description must contain at least 2 characters.",
      );
      return;
    }

    // Send the validated transfer to the backend.
    transferMutation.mutate({
      source_account_id: sourceAccountId,
      destination_account_id: destinationAccountId,
      amount: numericAmount,
      currency: sourceAccount.currency,
      description: description.trim(),
      transaction_date: transactionDate,
    });
  }

  return (
    <main className="min-h-screen space-y-8 bg-[#080b16] p-5 text-white md:p-8 lg:p-10">

      {/* Page heading */}
      <header>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-cyan-500/20 bg-cyan-500/10">
            <span className="text-xl font-bold text-cyan-400">
              ₹
            </span>
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">
              Money Transfers
            </h1>

            <p className="mt-1 text-sm text-gray-400">
              Move money between your accounts and track previous transfers.
            </p>
          </div>
        </div>
      </header>

      {/* Create transfer section */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-5 shadow-lg shadow-black/10 md:p-7">

        <div className="mb-7">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-white">
              Create a transfer
            </h2>

            <span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-cyan-400">
              Internal
            </span>
          </div>

          <p className="mt-2 text-sm text-gray-400">
            Select your accounts and enter the amount you want to transfer.
          </p>
        </div>

        {accountsQuery.isLoading ? (
          <div className="flex items-center gap-3 py-8 text-sm text-gray-400">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-700 border-t-cyan-400" />
            Loading your accounts...
          </div>
        ) : accountsQuery.isError ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            Unable to load accounts. Please refresh the page.
          </div>
        ) : accounts.length < 2 ? (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-300">
            You need at least two active accounts to make a transfer.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Source and destination accounts */}
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">

              <div>
                <label
                  htmlFor="sourceAccount"
                  className="mb-2 block text-sm font-medium text-gray-300"
                >
                  From account
                </label>

                <select
                  id="sourceAccount"
                  value={sourceAccountId}
                  onChange={(event) => {
                    const selectedId = event.target.value;

                    setSourceAccountId(selectedId);

                    // Prevent selecting the same account on both sides.
                    if (selectedId === destinationAccountId) {
                      setDestinationAccountId("");
                    }
                  }}
                  required
                  className={inputClass}
                >
                  <option value="" disabled>
                    Select source account
                  </option>

                  {accounts.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name} ({account.currency})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="destinationAccount"
                  className="mb-2 block text-sm font-medium text-gray-300"
                >
                  To account
                </label>

                <select
                  id="destinationAccount"
                  value={destinationAccountId}
                  onChange={(event) =>
                    setDestinationAccountId(event.target.value)
                  }
                  required
                  className={inputClass}
                >
                  <option value="" disabled>
                    Select destination account
                  </option>

                  {accounts
                    .filter(
                      (account) => account.id !== sourceAccountId,
                    )
                    .map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.name} ({account.currency})
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {/* Transfer direction preview */}
            {sourceAccount && destinationAccount && (
              <div className="flex flex-wrap items-center gap-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-4 py-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <span className="text-lg">↗</span>
                </div>

                <div className="flex flex-1 flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold text-white">
                    {sourceAccount.name}
                  </span>

                  <span className="text-cyan-400">→</span>

                  <span className="font-semibold text-white">
                    {destinationAccount.name}
                  </span>
                </div>

                <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300">
                  {sourceAccount.currency}
                </span>
              </div>
            )}

            {/* Amount and transfer date */}
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">

              <div>
                <label
                  htmlFor="transferAmount"
                  className="mb-2 block text-sm font-medium text-gray-300"
                >
                  Amount
                </label>

                <input
                  id="transferAmount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                  placeholder="Enter amount"
                  required
                  className={inputClass}
                />
              </div>

              <div>
                <label
                  htmlFor="transferDate"
                  className="mb-2 block text-sm font-medium text-gray-300"
                >
                  Transfer date
                </label>

                <input
                  id="transferDate"
                  type="date"
                  value={transactionDate}
                  onChange={(event) =>
                    setTransactionDate(event.target.value)
                  }
                  required
                  className={inputClass}
                />
              </div>
            </div>

            {/* Transfer description */}
            <div>
              <label
                htmlFor="transferDescription"
                className="mb-2 block text-sm font-medium text-gray-300"
              >
                Description
              </label>

              <input
                id="transferDescription"
                type="text"
                minLength={2}
                maxLength={255}
                value={description}
                onChange={(event) =>
                  setDescription(event.target.value)
                }
                placeholder="e.g. Monthly savings transfer"
                required
                className={inputClass}
              />
            </div>

            {/* Error message */}
            {errorMessage && (
              <div
                role="alert"
                className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400"
              >
                <span className="font-bold">!</span>
                <p>{errorMessage}</p>
              </div>
            )}

            {/* Success message */}
            {successMessage && (
              <div
                role="status"
                className="flex items-start gap-3 rounded-xl border border-green-500/20 bg-green-500/10 p-4 text-sm text-green-400"
              >
                <span className="font-bold">✓</span>
                <p>{successMessage}</p>
              </div>
            )}

            {/* Submit button */}
            <div className="flex flex-wrap items-center gap-4 border-t border-gray-800 pt-5">
              <button
                type="submit"
                disabled={transferMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-[#080b16] shadow-lg shadow-cyan-500/10 transition hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-[#111827] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {transferMutation.isPending ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#080b16]/30 border-t-[#080b16]" />
                    Processing transfer...
                  </>
                ) : (
                  <>
                    Transfer money
                    <span aria-hidden="true">→</span>
                  </>
                )}
              </button>

              <p className="text-xs text-gray-500">
                Transfers are processed securely between your accounts.
              </p>
            </div>

          </form>
        )}
      </section>

      {/* Transfer history section */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-5 shadow-lg shadow-black/10 md:p-7">

        <div className="mb-7 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Transfer history
            </h2>

            <p className="mt-2 text-sm text-gray-400">
              Review your recent account-to-account transfers.
            </p>
          </div>

          {transfersQuery.data && (
            <span className="rounded-full border border-gray-700 bg-[#080b16] px-3 py-1.5 text-xs font-medium text-gray-400">
              {transfersQuery.data.total} total transfers
            </span>
          )}
        </div>

        {transfersQuery.isLoading ? (
          <div className="flex items-center gap-3 py-10 text-sm text-gray-400">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-700 border-t-cyan-400" />
            Loading transfer history...
          </div>
        ) : transfersQuery.isError ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            Unable to load transfer history. Please try again.
          </div>
        ) : !transfersQuery.data?.items.length ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-700 bg-[#080b16]/50 px-4 py-14 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10 text-2xl text-cyan-400">
              ↗
            </div>

            <p className="font-semibold text-gray-200">
              No transfers yet
            </p>

            <p className="mt-2 max-w-sm text-sm text-gray-500">
              Your completed account-to-account transfers will appear here.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto rounded-xl border border-gray-800">
              <table className="w-full min-w-[700px] text-left text-sm text-gray-300">

                <thead>
                  <tr className="border-b border-gray-700 bg-[#080b16] text-xs uppercase tracking-wider text-gray-500">
                    <th className="px-5 py-4 font-semibold">
                      Date
                    </th>

                    <th className="px-5 py-4 font-semibold">
                      Description
                    </th>

                    <th className="px-5 py-4 font-semibold">
                      Transfer
                    </th>

                    <th className="px-5 py-4 text-right font-semibold">
                      Amount
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {transfersQuery.data.items.map((transfer) => {
                    const from = accounts.find(
                      (account) =>
                        account.id === transfer.source_account_id,
                    );

                    const to = accounts.find(
                      (account) =>
                        account.id === transfer.destination_account_id,
                    );

                    return (
                      <tr
                        key={transfer.id}
                        className="border-b border-gray-800 transition hover:bg-gray-800/40"
                      >
                        <td className="whitespace-nowrap px-5 py-5 text-gray-400">
                          {transfer.transaction_date}
                        </td>

                        <td className="px-5 py-5">
                          <p className="font-medium text-gray-200">
                            {transfer.description}
                          </p>
                        </td>

                        <td className="px-5 py-5">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-md bg-gray-800 px-2.5 py-1.5 text-xs font-medium text-gray-300">
                              {from?.name ?? "Source"}
                            </span>

                            <span className="text-cyan-400">
                              →
                            </span>

                            <span className="rounded-md bg-gray-800 px-2.5 py-1.5 text-xs font-medium text-gray-300">
                              {to?.name ?? "Destination"}
                            </span>
                          </div>
                        </td>

                        <td className="whitespace-nowrap px-5 py-5 text-right font-semibold text-white">
                          {formatMoney(
                            Number(transfer.amount),
                            transfer.currency,
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>

              </table>
            </div>

            {/* Transfer history footer */}
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-gray-800 pt-5">
              <p className="text-xs text-gray-500">
                Showing {transfersQuery.data.items.length} of{" "}
                {transfersQuery.data.total} transfers
              </p>

              <span className="flex items-center gap-2 text-xs text-green-400">
                <span className="h-2 w-2 rounded-full bg-green-400" />
                Transfer records synced
              </span>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
