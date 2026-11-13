"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Company } from "@/lib/types";
import { getCompanies, deleteCompany } from "@/lib/api";
import { CompanyCard } from "@/components/companies/CompanyCard";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Building2, Plus, Loader2, Search } from "lucide-react";

export default function CompaniesPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [companyToDelete, setCompanyToDelete] = useState<Company | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCompanies();
      setCompanies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (companyId: number) => {
    const company = companies.find((c) => c.id === companyId);
    if (company) setCompanyToDelete(company);
  };

  const confirmDelete = async () => {
    if (!companyToDelete) return;

    setDeleting(true);
    try {
      await deleteCompany(companyToDelete.id);
      setCompanies((prev) => prev.filter((c) => c.id !== companyToDelete.id));
      setCompanyToDelete(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete company");
    } finally {
      setDeleting(false);
    }
  };

  const handleEdit = (company: Company) => {
    router.push(`/companies/${company.id}`);
  };

  const filteredCompanies = companies.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.website?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="container mx-auto max-w-6xl py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Companies</h1>
          <p className="text-muted-foreground">Manage your company profiles for blog generation</p>
        </div>
        <Button onClick={() => router.push("/companies/new")}>
          <Plus className="mr-2 h-4 w-4" /> Create Company
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center gap-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search companies..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {filteredCompanies.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">
            {searchQuery ? "No companies found" : "No companies yet"}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            {searchQuery
              ? "Try a different search term"
              : "Create your first company to get started with blog generation"}
          </p>
          {!searchQuery && (
            <Button onClick={() => router.push("/companies/new")}>
              <Plus className="mr-2 h-4 w-4" /> Create Company
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredCompanies.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={companyToDelete !== null}
        onOpenChange={(open) => {
          if (!open) setCompanyToDelete(null);
        }}
        title="Delete Company"
        description={`Are you sure you want to delete "${companyToDelete?.name}"? This will also delete all associated projects. This cannot be undone.`}
        loading={deleting}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
