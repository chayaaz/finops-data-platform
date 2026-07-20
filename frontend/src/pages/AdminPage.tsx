import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatDateTime } from "@/lib/format";
import { clsx } from "clsx";
import type { UserRole } from "@/types/api";

const TABS = ["Users", "Data Quality Rules", "Audit Log"] as const;
type Tab = (typeof TABS)[number];

export function AdminPage() {
  const [tab, setTab] = useState<Tab>("Users");

  return (
    <div>
      <PageHeader title="Admin" description="User management, data-quality rule configuration, and audit trail" />

      <div className="mb-5 flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={clsx(
              "px-4 py-2.5 text-sm font-medium transition-colors",
              tab === t ? "border-b-2 border-brand-600 text-brand-600" : "text-slate-500 hover:text-slate-800"
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Users" && <UsersTab />}
      {tab === "Data Quality Rules" && <RulesTab />}
      {tab === "Audit Log" && <AuditTab />}
    </div>
  );
}

const roleTone: Record<UserRole, "brand" | "positive" | "warn" | "slate"> = {
  admin: "brand",
  finance_manager: "positive",
  analyst: "warn",
  auditor: "slate",
};

function UsersTab() {
  const queryClient = useQueryClient();
  const users = useQuery({ queryKey: ["admin-users"], queryFn: endpoints.admin.users });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", role: "analyst", password: "" });

  const createUser = useMutation({
    mutationFn: () => endpoints.admin.createUser(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setShowForm(false);
      setForm({ email: "", full_name: "", role: "analyst", password: "" });
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => endpoints.admin.updateUser(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <Button onClick={() => setShowForm((v) => !v)}>
          <Plus size={15} /> New User
        </Button>
      </div>

      {showForm && (
        <Card className="mb-4 p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createUser.mutate();
            }}
            className="grid grid-cols-1 gap-3 sm:grid-cols-4"
          >
            <input
              required
              placeholder="Full name"
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
            />
            <input
              required
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
            />
            <select
              value={form.role}
              onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
            >
              <option value="admin">Admin</option>
              <option value="finance_manager">Finance Manager</option>
              <option value="analyst">Analyst</option>
              <option value="auditor">Auditor</option>
            </select>
            <input
              required
              type="password"
              placeholder="Temporary password"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
            />
            <Button type="submit" disabled={createUser.isPending} className="sm:col-span-4 sm:w-40">
              {createUser.isPending ? "Creating…" : "Create User"}
            </Button>
          </form>
        </Card>
      )}

      {users.isLoading ? (
        <Spinner />
      ) : users.isError ? (
        <ErrorState message="Could not load users" />
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3">Name</th>
                <th className="px-2 py-3">Email</th>
                <th className="px-2 py-3">Role</th>
                <th className="px-2 py-3">Status</th>
                <th className="px-2 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.data?.map((u) => (
                <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-6 py-2.5 font-medium text-slate-800">{u.full_name}</td>
                  <td className="px-2 py-2.5 text-slate-600">{u.email}</td>
                  <td className="px-2 py-2.5">
                    <Badge tone={roleTone[u.role]}>{u.role.replace("_", " ")}</Badge>
                  </td>
                  <td className="px-2 py-2.5">
                    <Badge tone={u.is_active ? "positive" : "negative"}>{u.is_active ? "active" : "disabled"}</Badge>
                  </td>
                  <td className="px-2 py-2.5 text-right">
                    {u.role === "admin" && u.is_active ? (
                      <span className="text-xs text-slate-400">Admin accounts can't be disabled</span>
                    ) : (
                      <button
                        onClick={() => toggleActive.mutate({ id: u.id, is_active: !u.is_active })}
                        className="text-xs font-medium text-brand-600 hover:underline"
                      >
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function RulesTab() {
  const queryClient = useQueryClient();
  const rules = useQuery({ queryKey: ["admin-rules"], queryFn: endpoints.admin.rules });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => endpoints.admin.updateRule(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-rules"] }),
  });

  if (rules.isLoading) return <Spinner />;
  if (rules.isError) return <ErrorState message="Could not load data quality rules" />;
  if (!rules.data || rules.data.length === 0) return <EmptyState message="No rules configured" />;

  return (
    <Card>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-6 py-3">Code</th>
            <th className="px-2 py-3">Name</th>
            <th className="px-2 py-3">Severity</th>
            <th className="px-2 py-3 text-right">Threshold</th>
            <th className="px-2 py-3">Status</th>
            <th className="px-2 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rules.data.map((rule) => (
            <tr key={rule.id} className="border-b border-slate-50 hover:bg-slate-50">
              <td className="px-6 py-2.5 font-mono text-xs text-slate-600">{rule.code}</td>
              <td className="px-2 py-2.5 text-slate-800">{rule.name}</td>
              <td className="px-2 py-2.5">
                <Badge tone="warn">{rule.severity}</Badge>
              </td>
              <td className="px-2 py-2.5 text-right tabular text-slate-600">{rule.threshold ?? "—"}</td>
              <td className="px-2 py-2.5">
                <Badge tone={rule.is_active ? "positive" : "slate"}>{rule.is_active ? "active" : "inactive"}</Badge>
              </td>
              <td className="px-2 py-2.5 text-right">
                <button
                  onClick={() => toggleActive.mutate({ id: rule.id, is_active: !rule.is_active })}
                  className="text-xs font-medium text-brand-600 hover:underline"
                >
                  {rule.is_active ? "Deactivate" : "Activate"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function AuditTab() {
  const audit = useQuery({ queryKey: ["admin-audit"], queryFn: () => endpoints.admin.auditLog(0, 200) });

  if (audit.isLoading) return <Spinner />;
  if (audit.isError) return <ErrorState message="Could not load audit log" />;
  if (!audit.data || audit.data.length === 0) return <EmptyState message="No audit entries yet" />;

  return (
    <Card>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-6 py-3">Action</th>
            <th className="px-2 py-3">Entity</th>
            <th className="px-2 py-3">Details</th>
            <th className="px-2 py-3">When</th>
          </tr>
        </thead>
        <tbody>
          {audit.data.map((entry) => (
            <tr key={entry.id} className="border-b border-slate-50 hover:bg-slate-50">
              <td className="px-6 py-2.5 font-medium text-slate-800">{entry.action.replace(/_/g, " ")}</td>
              <td className="px-2 py-2.5 text-slate-600">
                {entry.entity_type}
                {entry.entity_id ? ` #${entry.entity_id}` : ""}
              </td>
              <td className="px-2 py-2.5 text-slate-500">{entry.details ?? "—"}</td>
              <td className="px-2 py-2.5 text-xs text-slate-500">{formatDateTime(entry.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
