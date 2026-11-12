"use client";

import { Company } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Trash2, Building2 } from "lucide-react";

interface Props {
  company: Company;
  onEdit?: (company: Company) => void;
  onDelete?: (companyId: number) => void;
  onSelect?: (company: Company) => void;
  showActions?: boolean;
  selectable?: boolean;
}

export function CompanyCard({ company, onEdit, onDelete, onSelect, showActions = true, selectable = false }: Props) {
  const handleClick = () => {
    if (onSelect) {
      onSelect(company);
    } else if (onEdit) {
      onEdit(company);
    }
  };

  return (
    <Card
      className={(onEdit || onSelect) ? "cursor-pointer hover:border-primary transition-colors" : ""}
      onClick={handleClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">{company.name}</CardTitle>
          </div>
          {showActions && (
            <div className="flex gap-2">
              {onEdit && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(company);
                  }}
                >
                  <Edit className="h-4 w-4" />
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(company.id);
                  }}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              )}
            </div>
          )}
        </div>
        {company.website && (
          <CardDescription>
            <a
              href={company.website}
              target="_blank"
              rel="noreferrer"
              className="hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {company.website}
            </a>
          </CardDescription>
        )}
      </CardHeader>
      {company.description && (
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-2">{company.description}</p>
        </CardContent>
      )}
      {selectable && onSelect && (
        <CardContent>
          <Button
            variant="outline"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(company);
            }}
          >
            Select Company
          </Button>
        </CardContent>
      )}
    </Card>
  );
}
