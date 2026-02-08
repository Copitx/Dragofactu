import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useAuthStore } from "@/stores/auth-store";
import { AppLayout } from "@/components/layout/app-layout";

const LoginPage = lazy(() => import("@/pages/auth/login"));
const RegisterPage = lazy(() => import("@/pages/auth/register"));
const DashboardPage = lazy(() => import("@/pages/dashboard"));
const ClientsPage = lazy(() => import("@/pages/clients"));
const ProductsPage = lazy(() => import("@/pages/products"));
const SuppliersPage = lazy(() => import("@/pages/suppliers"));
const DocumentsPage = lazy(() => import("@/pages/documents"));
const DocumentNewPage = lazy(() => import("@/pages/documents/new"));
const DocumentDetailPage = lazy(() => import("@/pages/documents/detail"));
const InventoryPage = lazy(() => import("@/pages/inventory"));
const WorkersPage = lazy(() => import("@/pages/workers"));
const DiaryPage = lazy(() => import("@/pages/diary"));
const RemindersPage = lazy(() => import("@/pages/reminders"));
const NotFoundPage = lazy(() => import("@/pages/not-found"));
const PlaceholderPage = lazy(() => import("@/pages/placeholder"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return (
    <AppLayout />
  );
}

function PublicRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}

const Loading = () => (
  <div className="min-h-screen flex items-center justify-center bg-background">
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
  </div>
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <Routes>
            {/* Public routes */}
            <Route element={<PublicRoute />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            {/* Protected routes with layout */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/clients" element={<ClientsPage />} />
              <Route path="/products" element={<ProductsPage />} />
              <Route path="/suppliers" element={<SuppliersPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/documents/new" element={<DocumentNewPage />} />
              <Route path="/documents/:id" element={<DocumentDetailPage />} />
              <Route path="/inventory" element={<InventoryPage />} />
              <Route path="/workers" element={<WorkersPage />} />
              <Route path="/diary" element={<DiaryPage />} />
              <Route path="/reminders" element={<RemindersPage />} />
              <Route path="/reports" element={<PlaceholderPage />} />
              <Route path="/settings" element={<PlaceholderPage />} />
              <Route path="/admin" element={<PlaceholderPage />} />
            </Route>

            {/* 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
