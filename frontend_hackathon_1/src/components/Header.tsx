import { useQuery } from "@tanstack/react-query";
import { authMe } from "../api/auth";

export function Header() {
  const { data: identity } = useQuery({ queryKey: ["auth-me"], queryFn: authMe });
  return (
    <header className="flex items-center justify-between px-6 py-4">
      <p className="text-sm font-semibold text-primary">{identity?.organization.name || "TrueHire"}</p>
      <div className="text-right">
        <p className="text-sm font-semibold text-foreground">{identity?.user.name || "Recruiter"}</p>
        <p className="text-xs text-muted-foreground">{identity?.user.email || ""}</p>
      </div>
    </header>
  );
}
