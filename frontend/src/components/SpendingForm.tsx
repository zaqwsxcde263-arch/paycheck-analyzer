import React, { useEffect, useState } from "react";
import { useAuthorizedApi } from "../api/client";

export interface Category {
  id: number;
  name: string;
  color: string;
}

export interface SpendingFormValues {
  id?: number;
  productName: string;
  amount: number;
  seller: string;
  date: string;
  categoryId: number;
  notes?: string;
}

interface SpendingFormProps {
  initial?: SpendingFormValues;
  onSaved: () => void;
  onCancel?: () => void;
}

export const SpendingForm: React.FC<SpendingFormProps> = ({ initial, onSaved, onCancel }) => {
  const api = useAuthorizedApi();
  const [categories, setCategories] = useState<Category[]>([]);
  const [values, setValues] = useState<SpendingFormValues>(
    initial ?? {
      productName: "",
      amount: 0,
      seller: "",
      date: new Date().toISOString().slice(0, 10),
      categoryId: 0,
      notes: ""
    }
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api
      .get<Category[]>("/categories")
      .then((res) => setCategories(res.data))
      .catch(() => setCategories([]));
  }, [api]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: name === "amount" || name === "categoryId" ? Number(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!values.productName.trim() || !values.seller.trim() || !values.date || !values.categoryId) {
      setError("Please fill all required fields.");
      return;
    }
    if (values.amount <= 0) {
      setError("Amount must be positive.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        productName: values.productName,
        amount: values.amount,
        seller: values.seller,
        date: values.date,
        categoryId: values.categoryId,
        notes: values.notes
      };
      if (values.id) {
        await api.put(`/spendings/${values.id}`, payload);
      } else {
        await api.post("/spendings", payload);
      }
      onSaved();
    } catch (err: any) {
      const message = err?.response?.data?.message ?? "Unable to save spending.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const amountInvalid = values.amount <= 0;

  return (
    <form className="spending-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label>
          Product
          <input
            name="productName"
            value={values.productName}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          Amount
          <input
            name="amount"
            type="number"
            step="0.01"
            value={values.amount}
            onChange={handleChange}
            className={amountInvalid ? "invalid" : ""}
            required
          />
        </label>
      </div>
      <div className="form-row">
        <label>
          Merchant
          <input name="seller" value={values.seller} onChange={handleChange} required />
        </label>
        <label>
          Date
          <input name="date" type="date" value={values.date} onChange={handleChange} required />
        </label>
      </div>
      <div className="form-row">
        <label>
          Category
          <select
            name="categoryId"
            value={values.categoryId}
            onChange={handleChange}
            required
          >
            <option value={0}>Select category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Notes
          <input name="notes" value={values.notes ?? ""} onChange={handleChange} />
        </label>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="form-actions">
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" disabled={loading}>
          {loading ? "Saving..." : "Save"}
        </button>
      </div>
    </form>
  );
};

