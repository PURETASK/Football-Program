import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { useSession } from '../auth/SessionContext';
import {
  fetchAdminWorkspace,
  fetchCollaborationWorkspace,
  fetchCollaborationStream,
  fetchFilmWorkspace,
  fetchGamePlanData,
  fetchGamePlanReleaseRoom,
  fetchAnalyticsWorkspace,
  fetchDeliveryWorkspace,
  fetchGovernanceInbox,
  fetchOperationsInbox,
  fetchRosterWorkspace,
  fetchPlayerToday,
  fetchPracticeWorkspace,
  fetchPracticeDrills,
  fetchPracticeAttendance,
  fetchScoutingWorkspace,
  fetchScoutingTendencies,
  fetchOrganizationPopulationReadiness,
  fetchStage25Acceptance,
} from '../lib/api';
import type { CollaborationActivity } from '../types';

type CollaborationStreamStatus = 'disabled' | 'connecting' | 'live' | 'reconnecting' | 'offline';

function parseServerEvent(block: string): { id?: number; event: string; data: string } | null {
  let id: number | undefined;
  let event = 'message';
  const data: string[] = [];
  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith('id:')) id = Number(line.slice(3).trim());
    else if (line.startsWith('event:')) event = line.slice(6).trim() || 'message';
    else if (line.startsWith('data:')) data.push(line.slice(5).trim());
  }
  if (!data.length) return null;
  return { id, event, data: data.join('\n') };
}

export function useCollaborationEventStream(): { status: CollaborationStreamStatus; lastEvent?: CollaborationActivity } {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<CollaborationStreamStatus>('disabled');
  const [lastEvent, setLastEvent] = useState<CollaborationActivity>();

  useEffect(() => {
    if (!session) {
      setStatus('disabled');
      return undefined;
    }
    let cancelled = false;
    let sequence = 0;
    let connected = false;
    let controller: AbortController | undefined;
    const wait = (milliseconds: number) => new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds));
    const consume = async () => {
      while (!cancelled) {
        setStatus(connected ? 'reconnecting' : 'connecting');
        controller = new AbortController();
        try {
          const response = await fetchCollaborationStream(session, sequence, controller.signal);
          if (!response.ok || !response.body) throw new Error(`Collaboration stream returned ${response.status}`);
          connected = true;
          setStatus('live');
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          let ended = false;
          while (!cancelled && !ended) {
            const chunk = await reader.read();
            if (chunk.done) break;
            buffer += decoder.decode(chunk.value, { stream: true });
            const blocks = buffer.split(/\r?\n\r?\n/);
            buffer = blocks.pop() ?? '';
            for (const block of blocks) {
              const parsed = parseServerEvent(block);
              if (!parsed) continue;
              if (parsed.id !== undefined && Number.isFinite(parsed.id)) sequence = Math.max(sequence, parsed.id);
              if (parsed.event === 'stream_end') { ended = true; break; }
              try {
                const event = JSON.parse(parsed.data) as CollaborationActivity;
                setLastEvent(event);
                void queryClient.invalidateQueries({ queryKey: ['collaboration-workspace', session.organizationId] });
                void queryClient.invalidateQueries({ queryKey: ['operations-inbox', session.organizationId] });
              } catch {
                // Ignore malformed events; replay resumes from the last valid sequence.
              }
            }
          }
        } catch {
          if (!cancelled) setStatus('offline');
        } finally {
          controller = undefined;
        }
        if (!cancelled) await wait(1500);
      }
    };
    void consume();
    return () => {
      cancelled = true;
      controller?.abort();
    };
  }, [queryClient, session?.organizationId, session?.token]);

  return { status, lastEvent };
}

export function useFilmWorkspaceQuery(query = '', enabled = true) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['film-workspace', session?.organizationId, query],
    queryFn: ({ signal }) => fetchFilmWorkspace(session!, query, signal),
    enabled: Boolean(session && enabled),
    staleTime: 15_000,
  });
}

export function usePracticeWorkspaceQuery(week = '', enabled = true) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['practice-workspace', session?.organizationId, week],
    queryFn: ({ signal }) => fetchPracticeWorkspace(session!, week, signal),
    enabled: Boolean(session && enabled),
    staleTime: 15_000,
  });
}

export function usePracticeDrillsQuery(filters: Record<string, string> = {}) {
  const { session } = useSession();
  const filterKey = Object.entries(filters).sort(([left], [right]) => left.localeCompare(right));
  return useQuery({
    queryKey: ['practice-drills', session?.organizationId, filterKey],
    queryFn: ({ signal }) => fetchPracticeDrills(session!, filters, signal),
    enabled: Boolean(session),
    staleTime: 60_000,
  });
}

export function usePracticeAttendanceQuery(practiceId = '') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['practice-attendance', session?.organizationId, practiceId],
    queryFn: ({ signal }) => fetchPracticeAttendance(session!, practiceId, signal),
    enabled: Boolean(session && practiceId),
    staleTime: 10_000,
  });
}

export function useScoutingWorkspaceQuery(opponent = '') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['scouting-workspace', session?.organizationId, opponent],
    queryFn: ({ signal }) => fetchScoutingWorkspace(session!, opponent, signal),
    enabled: Boolean(session),
    staleTime: 15_000,
  });
}

export function useScoutingTendencyQuery(filters: Record<string, string>, opponent = '', enabled = true) {
  const { session } = useSession();
  const filterKey = Object.entries(filters).sort(([left], [right]) => left.localeCompare(right));
  return useQuery({
    queryKey: ['scouting-tendency-explorer', session?.organizationId, opponent, filterKey],
    queryFn: ({ signal }) => fetchScoutingTendencies(session!, filters, opponent, signal),
    enabled: Boolean(session && enabled),
    staleTime: 10_000,
  });
}

export function useGamePlanDataQuery(week = '') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['game-plan-workspace', session?.organizationId, week],
    queryFn: ({ signal }) => fetchGamePlanData(session!, week, signal),
    enabled: Boolean(session),
    staleTime: 10_000,
  });
}

export function useGamePlanReleaseRoomQuery(week = '') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['game-plan-release-room', session?.organizationId, week],
    queryFn: ({ signal }) => fetchGamePlanReleaseRoom(session!, week, signal),
    enabled: Boolean(session),
    staleTime: 10_000,
  });
}

export function useAnalyticsWorkspaceQuery(situation = '') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['analytics-workspace', session?.organizationId, situation],
    queryFn: ({ signal }) => fetchAnalyticsWorkspace(session!, situation, signal),
    enabled: Boolean(session),
    staleTime: 15_000,
  });
}

export function useDeliveryWorkspaceQuery(week = '') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['delivery-workspace', session?.organizationId, week],
    queryFn: ({ signal }) => fetchDeliveryWorkspace(session!, week, signal),
    enabled: Boolean(session),
    staleTime: 10_000,
  });
}

export function usePlayerTodayQuery(playerId: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['player-today', session?.organizationId, playerId],
    queryFn: ({ signal }) => fetchPlayerToday(session!, playerId, signal),
    enabled: Boolean(session && playerId),
    staleTime: 10_000,
  });
}

export function useAdminWorkspaceQuery() {
  const { session } = useSession();
  return useQuery({
    queryKey: ['admin-workspace', session?.organizationId],
    queryFn: ({ signal }) => fetchAdminWorkspace(session!, signal),
    enabled: Boolean(session),
    staleTime: 20_000,
  });
}

export function useStage25AcceptanceQuery() {
  const { session } = useSession();
  return useQuery({
    queryKey: ['stage25-acceptance', session?.organizationId],
    queryFn: ({ signal }) => fetchStage25Acceptance(session!, signal),
    enabled: Boolean(session),
    staleTime: 20_000,
  });
}

export function useOrganizationPopulationReadinessQuery(season = '2026') {
  const { session } = useSession();
  return useQuery({
    queryKey: ['organization-population-readiness', session?.organizationId, season],
    queryFn: ({ signal }) => fetchOrganizationPopulationReadiness(session!, season, signal),
    enabled: Boolean(session),
    staleTime: 20_000,
  });
}

export function useGovernanceInboxQuery() {
  const { session } = useSession();
  return useQuery({
    queryKey: ['governance-inbox', session?.organizationId, session?.role],
    queryFn: ({ signal }) => fetchGovernanceInbox(session!, signal),
    enabled: Boolean(session),
    staleTime: 10_000,
  });
}

export function useOperationsInboxQuery(filters: Record<string, string> = {}) {
  const { session } = useSession();
  const filterKey = Object.entries(filters).sort(([left], [right]) => left.localeCompare(right));
  return useQuery({
    queryKey: ['operations-inbox', session?.organizationId, session?.subject, filterKey],
    queryFn: ({ signal }) => fetchOperationsInbox(session!, filters, signal),
    enabled: Boolean(session),
    staleTime: 5_000,
  });
}

export function useCollaborationWorkspaceQuery(filters: Record<string, string> = {}) {
  const { session } = useSession();
  const filterKey = Object.entries(filters).sort(([left], [right]) => left.localeCompare(right));
  return useQuery({
    queryKey: ['collaboration-workspace', session?.organizationId, session?.subject, filterKey],
    queryFn: ({ signal }) => fetchCollaborationWorkspace(session!, filters, signal),
    enabled: Boolean(session),
    staleTime: 5_000,
  });
}

export function useRosterWorkspaceQuery(filters: Record<string, string> = {}, enabled = true) {
  const { session } = useSession();
  const filterKey = Object.entries(filters).sort(([left], [right]) => left.localeCompare(right));
  return useQuery({
    queryKey: ['roster-workspace', session?.organizationId, session?.subject, filterKey],
    queryFn: ({ signal }) => fetchRosterWorkspace(session!, filters, signal),
    enabled: Boolean(session && enabled),
    staleTime: 15_000,
  });
}
