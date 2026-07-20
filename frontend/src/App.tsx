import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/context/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { UploadPage } from "@/pages/UploadPage";
import { IngestionMonitorPage } from "@/pages/IngestionMonitorPage";
import { DataQualityPage } from "@/pages/DataQualityPage";
import { AnomaliesPage } from "@/pages/AnomaliesPage";
import { TransactionsPage } from "@/pages/TransactionsPage";
import { BudgetsPage } from "@/pages/BudgetsPage";
import { VendorsPage } from "@/pages/VendorsPage";
import { AllocationPage } from "@/pages/AllocationPage";
import { TrendsForecastPage } from "@/pages/TrendsForecastPage";
import { FxExposurePage } from "@/pages/FxExposurePage";
import { AdminPage } from "@/pages/AdminPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/ingestion" element={<IngestionMonitorPage />} />
              <Route path="/quality" element={<DataQualityPage />} />
              <Route path="/anomalies" element={<AnomaliesPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/budgets" element={<BudgetsPage />} />
              <Route path="/vendors" element={<VendorsPage />} />
              <Route path="/allocation" element={<AllocationPage />} />
              <Route path="/trends" element={<TrendsForecastPage />} />
              <Route path="/fx-exposure" element={<FxExposurePage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
