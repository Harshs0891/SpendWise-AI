import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { csvApi } from "../features/csv/CsvApi";
import type { CsvExportFilters } from "../features/csv/CsvTypes";

import { accountApi } from "../features/accounts/AccountApi";
import { categoryApi } from "../features/categories/CategoryApi";

import type { TransactionType } from "../features/transactions/TransactionTypes";

interface ImportRowError {
  row: number;
  errors: string[];
}

// Extract validation errors returned by the backend.
function getImportError(error: unknown): {
  message: string;
  rowErrors: ImportRowError[];
} {
  if (typeof error !== "object" || error === null || !("response" in error)) {
    return {
      message: "Unable to import the CSV file. Please try again.",
      rowErrors: [],
    };
  }

  const response = (error as {
    response?: {
      status?: number;
      data?: unknown;
    };
  }).response;

  const data = response?.data;

  // Handle a FastAPI validation response.
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;

    if (typeof detail === "object" && detail !== null && !Array.isArray(detail)) {
      const validation = detail as {
        message?: string;
        row_errors?: ImportRowError[];
      };

      return {
        message: validation.message ?? "CSV validation failed.",
        rowErrors: validation.row_errors ?? [],
      };
    }

    if (Array.isArray(detail)) {
      return {
        message: detail
          .map((item) => item.msg ?? "Invalid request")
          .join("; "),
        rowErrors: [],
      };
    }

    if (typeof detail === "string") {
      return { message: detail, rowErrors: [] };
    }
  }

  return {
    message: `Import failed (HTTP ${response?.status ?? "unknown"}). Check the browser Network response for details.`,
    rowErrors: [],
  };
}

export default function CsvManagement() {
  const queryClient = useQueryClient();

  // Export filter state.
  const [type, setType] = useState<"" | TransactionType>("");
  const [accountId, setAccountId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Import file and feedback state.
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importSuccess, setImportSuccess] = useState("");
  const [importError, setImportError] = useState("");
  const [rowErrors, setRowErrors] = useState<ImportRowError[]>([]);

  // Load accounts and categories for the export filters.
  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: accountApi.getAll,
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories", "all"],
    queryFn: () => categoryApi.getAll(),
  });

  // Download the filtered transaction CSV.
  const exportMutation = useMutation({
    mutationFn: (filters: CsvExportFilters) =>
      csvApi.exportTransactions(filters),

    onSuccess: (blob) => {
      // Create a temporary browser URL for the downloaded CSV.
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = downloadUrl;
      link.download = "spendwise_transactions.csv";

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(downloadUrl);
    },
  });

  // Upload and import the selected CSV file.
  const importMutation = useMutation({
    mutationFn: (file: File) => csvApi.importTransactions(file),

    onSuccess: async (result) => {
      setImportSuccess(
        `Successfully imported ${result.imported_count} transaction(s).`,
      );

      setImportError("");
      setRowErrors([]);
      setSelectedFile(null);

      // Refresh financial data affected by the imported transactions.
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["accounts"] }),
      ]);
    },

    onError: (error: unknown) => {
      const result = getImportError(error);

      setImportSuccess("");
      setImportError(result.message);
      setRowErrors(result.rowErrors);
    },
  });

  function handleExport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (startDate && endDate && startDate > endDate) {
      return;
    }

    const filters: CsvExportFilters = {
      type: type || undefined,
      account_id: accountId || undefined,
      category_id: categoryId || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    };

    exportMutation.mutate(filters);
  }

  function handleImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setImportError("");
    setImportSuccess("");
    setRowErrors([]);

    if (!selectedFile) {
      setImportError("Please select a CSV file first.");
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setImportError("Only .csv files are supported.");
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setImportError("File size must not exceed 5 MB.");
      return;
    }

    importMutation.mutate(selectedFile);
  }

  return (
    <main className="min-h-screen space-y-8 bg-[#080b16] p-6 text-white md:p-10">
      {/* Page heading */}
      <header>
        <h1 className="text-3xl font-bold">CSV Import & Export</h1>
        <p className="mt-2 text-sm text-gray-400">
          Import transactions from a CSV file or export your financial records.
        </p>
      </header>

      {/* Export section */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold">Export Transactions</h2>
          <p className="mt-1 text-sm text-gray-400">
            Select optional filters to download specific transactions.
          </p>
        </div>

        <form onSubmit={handleExport} className="space-y-5">
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">
                Transaction type
              </label>

              <select
                value={type}
                onChange={(event) =>
                  setType(event.target.value as "" | TransactionType)
                }
                className="w-full rounded-lg border border-gray-700 bg-[#080b16] px-3 py-3 text-white outline-none focus:border-cyan-500"
              >
                <option value="">All types</option>
                <option value="income">Income</option>
                <option value="expense">Expense</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">
                Account
              </label>

              <select
                value={accountId}
                onChange={(event) => setAccountId(event.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-[#080b16] px-3 py-3 text-white outline-none focus:border-cyan-500"
              >
                <option value="">All accounts</option>

                {accountsQuery.data?.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">
                Category
              </label>

              <select
                value={categoryId}
                onChange={(event) => setCategoryId(event.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-[#080b16] px-3 py-3 text-white outline-none focus:border-cyan-500"
              >
                <option value="">All categories</option>

                {categoriesQuery.data?.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name} ({category.kind})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-300">
                  Start date
                </label>

                <input
                  type="date"
                  value={startDate}
                  max={endDate || undefined}
                  onChange={(event) => setStartDate(event.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-[#080b16] px-3 py-3 text-white outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-300">
                  End date
                </label>

                <input
                  type="date"
                  value={endDate}
                  min={startDate || undefined}
                  onChange={(event) => setEndDate(event.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-[#080b16] px-3 py-3 text-white outline-none focus:border-cyan-500"
                />
              </div>
            </div>
          </div>

          {startDate && endDate && startDate > endDate && (
            <p className="text-sm text-red-400">
              Start date cannot be later than end date.
            </p>
          )}

          {exportMutation.isError && (
            <p role="alert" className="text-sm text-red-400">
              Export failed. Please try again.
            </p>
          )}

          <button
            type="submit"
            disabled={
              exportMutation.isPending ||
              Boolean(startDate && endDate && startDate > endDate)
            }
            className="rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-black transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {exportMutation.isPending ? "Preparing CSV..." : "Download CSV"}
          </button>
        </form>
      </section>

      {/* Import section */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold">Import Transactions</h2>
          <p className="mt-1 text-sm text-gray-400">
            Upload a CSV file to add transactions to your SpendWise account.
          </p>
        </div>

        <form onSubmit={handleImport} className="space-y-5">
          <div className="rounded-xl border-2 border-dashed border-gray-700 bg-[#080b16] p-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400">
              <span className="text-2xl">↑</span>
            </div>

            <label
              htmlFor="csvFile"
              className="cursor-pointer font-medium text-cyan-400 hover:text-cyan-300"
            >
              Choose a CSV file
            </label>

            <p className="mt-2 text-xs text-gray-500">
              CSV format only · Maximum file size 5 MB
            </p>

            <input
              id="csvFile"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                setSelectedFile(event.target.files?.[0] ?? null);
                setImportError("");
                setImportSuccess("");
                setRowErrors([]);
              }}
              className="sr-only"
            />

            {selectedFile && (
              <div className="mx-auto mt-5 max-w-md rounded-lg border border-gray-700 bg-[#111827] p-3 text-left">
                <p className="truncate text-sm font-medium text-white">
                  {selectedFile.name}
                </p>

                <p className="mt-1 text-xs text-gray-400">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-gray-800 bg-[#080b16] p-4">
            <h3 className="text-sm font-semibold text-gray-200">
              Required CSV columns
            </h3>

            <p className="mt-2 text-xs leading-6 text-gray-400">
              account_id, type, amount, currency, description,
              transaction_date
            </p>

            <p className="mt-2 text-xs text-gray-500">
              Optional columns: id, category_id, merchant, notes.
            </p>
          </div>

          {importSuccess && (
            <div
              role="status"
              className="rounded-lg border border-green-800 bg-green-500/10 p-4 text-sm text-green-400"
            >
              {importSuccess}
            </div>
          )}

          {importError && (
            <div
              role="alert"
              className="rounded-lg border border-red-800 bg-red-500/10 p-4"
            >
              <p className="text-sm font-medium text-red-400">
                {importError}
              </p>

              {rowErrors.length > 0 && (
                <div className="mt-4 space-y-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-red-300">
                    Row validation errors
                  </p>

                  {rowErrors.map((item, index) => (
                    <div
                      key={`${item.row}-${index}`}
                      className="rounded-md bg-red-950/40 p-3"
                    >
                      <p className="text-sm font-semibold text-red-300">
                        Row {item.row}
                      </p>

                      <ul className="mt-1 list-inside list-disc space-y-1">
                        {item.errors.map((message, errorIndex) => (
                          <li
                            key={errorIndex}
                            className="text-xs text-red-200"
                          >
                            {message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={!selectedFile || importMutation.isPending}
            className="rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {importMutation.isPending ? "Importing transactions..." : "Import CSV"}
          </button>
        </form>
      </section>
    </main>
  );
}