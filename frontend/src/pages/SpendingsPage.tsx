import React, { useEffect, useState } from "react";
import { useAuthorizedApi } from "../api/client";
import { useAuth } from "../state/AuthContext";
import { SpendingForm, SpendingFormValues } from "../components/SpendingForm";
import { ConfirmDialog } from "../components/ConfirmDialog";

interface Spending {
  id: number;
  productName: string;
  amount: number;
  seller: string;
  date: string;
  category: {
    id: number;
    name: string;
    color: string;
  };
  notes?: string;
}

export const SpendingsPage: React.FC = () => {
  const api = useAuthorizedApi();
  const { logout } = useAuth();
  const [spendings, setSpendings] = useState<Spending[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Spending | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Spending | null>(null);

  const fetchSpendings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<Spending[]>("/spendings", {
        params: {
          month: new Date().toISOString().slice(0, 7),
          sort: "date",
          order: "desc"
        }
      });
      setSpendings(response.data);
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 401) {
        logout();
      } else {
        setError("Unable to load spendings.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpendings();
  }, []);

  const handleEditClick = (s: Spending) => {
    setEditing(s);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/spendings/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchSpendings();
    } catch {
      setError("Failed to delete spending.");
    }
  };

  const toFormValues = (s: Spending): SpendingFormValues => ({
    id: s.id,
    productName: s.productName,
    amount: s.amount,
    seller: s.seller,
    date: s.date,
    categoryId: s.category.id,
    notes: s.notes
  });

  return (
    <div className="page">
      <header className="page-header">
        <h1>Spendings</h1>
      </header>
      <section className="card">
        <h2>{editing ? "Edit spending" : "Add spending"}</h2>
        <SpendingForm
          initial={editing ? toFormValues(editing) : undefined}
          onSaved={() => {
            setEditing(null);
            fetchSpendings();
          }}
          onCancel={() => setEditing(null)}
        />
      </section>
      <section className="card">
        <h2>Recent spendings</h2>
        {loading && <p>Loading...</p>}
        {error && <div className="error-banner">{error}</div>}
        {!loading && !error && (
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Product</th>
                <th>Category</th>
                <th>Amount</th>
                <th>Merchant</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {spendings.map((s) => (
                <tr key={s.id}>
                  <td>{s.date}</td>
                  <td>{s.productName}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: s.category.color }}>
                      {s.category.name}
                    </span>
                  </td>
                  <td>${s.amount.toFixed(2)}</td>
                  <td>{s.seller}</td>
                  <td>
                    <button className="link" onClick={() => handleEditClick(s)}>
                      Edit
                    </button>
                    <button className="link danger" onClick={() => setDeleteTarget(s)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <ConfirmDialog
        title="Delete spending"
        message="Are you sure you want to delete this spending? This action cannot be undone."
        open={!!deleteTarget}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
};

