import DashboardPageClient from "./DashboardPageClient";  // 그냥 불러오기

export const metadata = { title: "AI Trading Dashboard" };

export default function Page() {
  // 서버 Render 단계에선 껍데기만 뿌리고,
  // DashboardPageClient 는 브라우저에서 하이드레이션됩니다.
  return <DashboardPageClient />;
}
