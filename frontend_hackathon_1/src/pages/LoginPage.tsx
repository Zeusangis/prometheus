import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { login } from "../api/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (identity) => {
      queryClient.clear();
      queryClient.setQueryData(["auth-me"], identity);
      navigate({ to: "/dashboard/jobs" });
    },
  });
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <form onSubmit={(event) => { event.preventDefault(); mutation.mutate(); }} className="w-full max-w-md space-y-5 rounded-3xl border border-border bg-card p-8">
        <p className="font-semibold text-primary">TrueHire</p>
        <h1 className="text-2xl font-semibold">Recruiter sign in</h1>
        <label className="block">Email
          <input aria-label="Email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-xl border p-3" />
        </label>
        <label className="block">Password
          <input aria-label="Password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-xl border p-3" />
        </label>
        {mutation.error && <p role="alert" className="text-sm text-red-700">{mutation.error.message}</p>}
        <button disabled={mutation.isPending} className="w-full rounded-xl bg-primary p-3 font-semibold text-white disabled:opacity-50">{mutation.isPending ? "Signing in…" : "Sign in"}</button>
        <p className="text-xs text-muted-foreground">Accounts are created by your TrueHire administrator.</p>
      </form>
    </main>
  );
}
