import { Navigate, useParams } from "@tanstack/react-router";

/**
 * Legacy route. The truthful applicant profile lives at /profile/$candidateId,
 * so this keeps old links working instead of rendering a placeholder screen.
 */
export default function CandidateDetail() {
  const { candidateId } = useParams({ from: "/candidate/$candidateId" });

  return (
    <Navigate
      to="/profile/$candidateId"
      params={{ candidateId }}
      replace
    />
  );
}
