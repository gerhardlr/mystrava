import { DashboardLayout } from "@toolpad/core/DashboardLayout";
import { PageContainer } from "@toolpad/core/PageContainer";
import PoweredByStrava from "@/components/PoweredByStrava";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardLayout>
      <PageContainer>{children}</PageContainer>
      <PoweredByStrava />
    </DashboardLayout>
  );
}
