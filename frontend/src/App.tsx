import { lazy, Suspense, type ComponentType } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/AppShell';
import { PlaybookPage } from './pages/PlaybookPage';
import { TodayPage } from './pages/TodayPage';

const PlayDesignerPage = lazy(() => import('./pages/PlayDesignerPage').then((module) => ({ default: module.PlayDesignerPage })));
const FilmPage = lazy(() => import('./pages/FilmPage').then((module) => ({ default: module.FilmPage })));
const PracticePage = lazy(() => import('./pages/PracticePage').then((module) => ({ default: module.PracticePage })));
const ScoutingPage = lazy(() => import('./pages/ScoutingPage').then((module) => ({ default: module.ScoutingPage })));
const GamePlanPage = lazy(() => import('./pages/GamePlanPage').then((module) => ({ default: module.GamePlanPage })));
const PlayerPage = lazy(() => import('./pages/PlayerPage').then((module) => ({ default: module.PlayerPage })));
const AdminPage = lazy(() => import('./pages/AdminPage').then((module) => ({ default: module.AdminPage })));
const Stage25AcceptancePage = lazy(() => import('./pages/Stage25AcceptancePage').then((module) => ({ default: module.Stage25AcceptancePage })));
const PopulationReadinessPage = lazy(() => import('./pages/PopulationReadinessPage').then((module) => ({ default: module.PopulationReadinessPage })));
const ReviewsPage = lazy(() => import('./pages/ReviewsPage').then((module) => ({ default: module.ReviewsPage })));
const OperationsInboxPage = lazy(() => import('./pages/OperationsInboxPage').then((module) => ({ default: module.OperationsInboxPage })));
const RosterPage = lazy(() => import('./pages/RosterPage').then((module) => ({ default: module.RosterPage })));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage })));
const DeliveryPage = lazy(() => import('./pages/DeliveryPage').then((module) => ({ default: module.DeliveryPage })));
const CollaborationPage = lazy(() => import('./pages/CollaborationPage').then((module) => ({ default: module.CollaborationPage })));

function RouteLoader({ label }: { label: string }) {
  return <div className="route-loader" role="status">Opening {label}…</div>;
}

function workspaceRoute(Page: ComponentType, label: string) {
  return <Suspense fallback={<RouteLoader label={label} />}><Page /></Suspense>;
}

export function App() {
  return (
    <Routes>
      <Route
        path="playbook/designer/:designId"
        element={(
          <Suspense fallback={<div className="designer-route-state" role="status">Opening the play workspace…</div>}>
            <PlayDesignerPage />
          </Suspense>
        )}
      />
      <Route element={<AppShell />}>
        <Route index element={<TodayPage />} />
        <Route path="inbox" element={workspaceRoute(OperationsInboxPage, 'Operations Inbox')} />
        <Route path="roster" element={workspaceRoute(RosterPage, 'Roster & Personnel')} />
        <Route path="analytics" element={workspaceRoute(AnalyticsPage, 'Outcome Analytics')} />
        <Route path="delivery" element={workspaceRoute(DeliveryPage, 'Game-week Delivery')} />
        <Route path="collaboration" element={workspaceRoute(CollaborationPage, 'Staff Collaboration')} />
        <Route path="playbook" element={<PlaybookPage />} />
        <Route path="film" element={workspaceRoute(FilmPage, 'Film Room')} />
        <Route path="practice" element={workspaceRoute(PracticePage, 'Practice')} />
        <Route path="scouting" element={workspaceRoute(ScoutingPage, 'Scouting')} />
        <Route path="game-plan" element={workspaceRoute(GamePlanPage, 'Game Plan')} />
        <Route path="player" element={workspaceRoute(PlayerPage, 'Player Development')} />
        <Route path="admin/stage-25" element={workspaceRoute(Stage25AcceptancePage, 'Stage 25 specification acceptance')} />
        <Route path="admin/population-readiness" element={workspaceRoute(PopulationReadinessPage, 'Organization population readiness')} />
        <Route path="admin" element={workspaceRoute(AdminPage, 'Admin & Governance')} />
        <Route path="reviews" element={workspaceRoute(ReviewsPage, 'Reviews & Approvals')} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Route>
    </Routes>
  );
}
