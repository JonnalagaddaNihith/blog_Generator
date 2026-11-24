"use client";

import { useState, useEffect, useCallback } from "react";
import { Company } from "@/lib/types";
import { getCompanies } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Building2, Plus, Loader2 } from "lucide-react";
import { CreateCompanyDialog } from "./CreateCompanyDialog";

interface Props {
  onSelect: (company: Company) => void;
  selectedCompanyId?: number;
}

export function CompanySelector({ onSelect, selectedCompanyId }: Props) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  const loadCompanies = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getCompanies();
      setCompanies(data);
    } catch (err) {
      console.error("Failed to load companies:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch on mount
    loadCompanies();
  }, [loadCompanies]);

  const handleCreated = (company: Company) => {
    setCompanies((prev) => [...prev, company]);
    onSelect(company);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (companies.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Companies Yet</h3>
          <p className="text-sm text-muted-foreground mb-4">Create your first company to get started</p>
          <CreateCompanyDialog
            trigger={
              <Button>
                <Plus className="mr-2 h-4 w-4" /> Create Company
              </Button>
            }
            onCreated={handleCreated}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Select a Company</h3>
        <CreateCompanyDialog
          trigger={
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" /> New Company
            </Button>
          }
          onCreated={handleCreated}
        />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {companies.map((company) => (
          <Card
            key={company.id}
            className={`cursor-pointer transition-colors ${
              selectedCompanyId === company.id ? "border-primary ring-2 ring-primary/20" : "hover:border-primary/50"
            }`}
            onClick={() => onSelect(company)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{company.name}</span>
                </div>
                {selectedCompanyId === company.id && <Badge variant="default">Selected</Badge>}
              </div>
              {company.website && (
                <p className="text-xs text-muted-foreground mb-2 truncate">{company.website}</p>
              )}
              {company.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">{company.description}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
