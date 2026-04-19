import { useParams } from "@tanstack/react-router";

export default function CandidateDetail() {
  const { candidateId } = useParams({ from: "/candidate/$candidateId" });

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto bg-card border border-border rounded-2xl p-6">
        <h1 className="text-2xl font-bold text-foreground">Candidate Detail</h1>
        <p className="text-muted-foreground mt-2">
          Viewing candidate ID: {candidateId}
        </p>
      </div>
    </main>
  );
}
