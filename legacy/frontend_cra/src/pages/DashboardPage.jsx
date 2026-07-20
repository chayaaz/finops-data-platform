import React, { useEffect, useState } from "react";
import { fetchSummary } from "../services/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchSummary().then(setSummary);
  }, []);

  if (!summary) return <div>Loading...</div>;

  return (
    <div style={{ padding: "20px" }}>
      <h1>FinOps Dashboard</h1>

      <p>Total Raw Records: {summary.total_raw}</p>
      <p>Total Clean Records: {summary.total_clean}</p>
      <p>Total Issues: {summary.total_issues}</p>

      <h2>Top Vendors</h2>
      <ul>
        {summary.top_vendors.map((vendor, index) => (
          <li key={index}>
            {vendor.vendor_name} - {vendor.total}
          </li>
        ))}
      </ul>
    </div>
  );
}