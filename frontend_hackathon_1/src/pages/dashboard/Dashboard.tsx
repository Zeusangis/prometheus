import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";
import { Dashboard as DashboardContent } from "../../components/Dashboard";

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <DashboardContent />
      </div>
    </div>
  );
}
