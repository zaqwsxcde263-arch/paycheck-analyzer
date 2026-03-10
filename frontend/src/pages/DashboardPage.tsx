import React, { useEffect, useMemo, useState } from "react";
import { useAuthorizedApi } from "../api/client";
import { useAuth } from "../state/AuthContext";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

interface CategorySummary {
  categoryId: number;
  categoryName: string;
  color: string;
  total: number;
  percentage: number;
}

interface DailySpending {
  date: string;
  total: number;
  outlier: boolean;
}

interface CumulativePoint {
  date: string;
  categories: Record<string, number>;
}

interface TopPurchase {
  id: number;
  productName: string;
  amount: number;
  categoryName: string;
  date: string;
}

interface ProductItem {
  id: number;
  name: string;
}

interface DashboardSummary {
  month: string;
  totalSpending: number;
  averageDaily: number;
  categories: CategorySummary[];
  dailySpending: DailySpending[];
  cumulative: CumulativePoint[];
  topPurchases: TopPurchase[];
  products: ProductItem[];
}

interface ProductHistory {
  productName: string;
  history: { date: string; amount: number }[];
}

export const DashboardPage: React.FC = () => {
  const api = useAuthorizedApi();
  const { logout } = useAuth();
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [productHistory, setProductHistory] = useState<ProductHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<DashboardSummary>("/dashboard/summary", {
        params: { month }
      });
      setSummary(response.data);
      setSelectedCategoryId(null);
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 401) {
        logout();
      } else {
        setError("Unable to load dashboard data.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [month]);

  useEffect(() => {
    if (!selectedProductId) {
      setProductHistory(null);
      return;
    }
    api
      .get<ProductHistory>("/dashboard/product-history", {
        params: { productId: selectedProductId, months: 6 }
      })
      .then((res) => setProductHistory(res.data))
      .catch(() => setProductHistory(null));
  }, [selectedProductId]);

  const filteredCategories = useMemo(() => {
    if (!summary) return [];
    if (!selectedCategoryId) return summary.categories;
    return summary.categories.filter((c) => c.categoryId === selectedCategoryId);
  }, [summary, selectedCategoryId]);

  const filteredDaily = useMemo(() => {
    if (!summary) return [];
    if (!selectedCategoryId) return summary.dailySpending;
    return summary.dailySpending;
  }, [summary, selectedCategoryId]);

  const stackedData = useMemo(() => {
    if (!summary) return [];
    return summary.cumulative.map((p) => ({
      date: p.date,
      ...p.categories
    }));
  }, [summary]);

  const categoryColors = useMemo(() => {
    const map: Record<string, string> = {};
    summary?.categories.forEach((c) => {
      map[c.categoryId.toString()] = c.color;
    });
    return map;
  }, [summary]);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Dashboard</h1>
        <div className="page-header-actions">
          <label>
            Month
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
            />
          </label>
        </div>
      </header>
      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading...</p>}
      {!loading && summary && (
        <>
          <section className="grid">
            <div className="card">
              <h2>By category</h2>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={filteredCategories}
                    dataKey="total"
                    nameKey="categoryName"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    onClick={(data) =>
                      setSelectedCategoryId(
                        selectedCategoryId === data.categoryId ? null : data.categoryId
                      )
                    }
                  >
                    {filteredCategories.map((c) => (
                      <cell key={c.categoryId} fill={c.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h2>Daily spending</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={filteredDaily}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="total"
                    name="Total"
                    shape={(props: any) => {
                      const color = props.payload.outlier ? "#ef4444" : "#3b82f6";
                      return <rect {...props} fill={color} />;
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey={() => summary.averageDaily}
                    stroke="#10b981"
                    dot={false}
                    name="Average"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="grid">
            <div className="card">
              <h2>Cumulative by category</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={stackedData} stackOffset="none">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  {Object.keys(categoryColors).map((id) => (
                    <Bar
                      key={id}
                      dataKey={id}
                      stackId="1"
                      name={summary.categories.find((c) => c.categoryId.toString() === id)?.categoryName}
                      fill={categoryColors[id]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h2>Top 10 purchases</h2>
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.topPurchases.map((p) => (
                    <tr key={p.id} onClick={() => setSelectedProductId(p.id)}>
                      <td>{p.date}</td>
                      <td>{p.productName}</td>
                      <td>{p.categoryName}</td>
                      <td>${p.amount.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card">
            <h2>Product price history</h2>
            <div className="form-row">
              <label>
                Product
                <select
                  value={selectedProductId ?? ""}
                  onChange={(e) =>
                    setSelectedProductId(e.target.value ? Number(e.target.value) : null)
                  }
                >
                  <option value="">Select product</option>
                  {summary.products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {productHistory && (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={productHistory.history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="amount" name="Price" stroke="#6366f1" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </section>
        </>
      )}
    </div>
  );
};

