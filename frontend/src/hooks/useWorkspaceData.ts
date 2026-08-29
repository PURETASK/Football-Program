import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { useSession } from '../auth/SessionContext';
import { acceptSequencedEvent } from './sequencedStream';
import {
  fetchOperatorSummary,
  fetchPlayAssets,
  fetchPlayPositionOptions,
  fetchPlayComments,
  fetchPlayDesigns,
  fetchPlayLegality,
  fetchPlayRuleProfiles,
  fetchPlayRoleView,
  fetchPlayPresence,
  fetchPlayCollaborationStream,
  fetchPlayTemplates,
  fetchPlayVariantBatches,
  fetchPlayVersionDiff,
  fetchPlayVersions,
  validatePlayDesignDraft,
} from '../lib/api';
import type { PlayCollaborationEvent, PlayDesign } from '../types';

function compactFingerprint(value: unknown): string {
  const serialized = JSON.stringify(value);
  let hash = 2166136261;
  for (let index = 0; index < serialized.length; index += 1) {
    hash ^= serialized.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `${serialized.length}:${(hash >>> 0).toString(36)}`;
}

export function useOperatorSummaryQuery() {
  const { session } = useSession();
  return useQuery({
    queryKey: ['operator-summary', session?.organizationId, session?.token],
    queryFn: ({ signal }) => fetchOperatorSummary(session!, signal),
    enabled: Boolean(session),
    staleTime: 30_000,
  });
}

export function usePlayDesignsQuery(enabled = true) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-designs', session?.organizationId, session?.token],
    queryFn: ({ signal }) => fetchPlayDesigns(session!, signal),
    enabled: Boolean(session && enabled),
    staleTime: 20_000,
  });
}

export function usePlayAssetsQuery(context?: Pick<PlayDesign, 'unit' | 'formation' | 'personnel' | 'rule_profile'>) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-assets', session?.organizationId, context?.unit, context?.formation, context?.personnel, context?.rule_profile],
    queryFn: ({ signal }) => fetchPlayAssets(session!, context, signal),
    enabled: Boolean(session),
    staleTime: 5 * 60_000,
  });
}

export function usePlayPositionOptionsQuery(player: { position?: string; role?: string; alignment_key?: string } | undefined, context: Pick<PlayDesign, 'unit' | 'formation' | 'personnel' | 'rule_profile'>) {
  const { session } = useSession();
  const position = player?.position ?? player?.role ?? player?.alignment_key ?? '';
  return useQuery({
    queryKey: ['play-position-options', session?.organizationId, position, context.unit, context.formation, context.personnel, context.rule_profile],
    queryFn: ({ signal }) => fetchPlayPositionOptions(session!, position, context, signal),
    enabled: Boolean(session && position),
    staleTime: 5 * 60_000,
    retry: 1,
  });
}

export function usePlayRuleProfilesQuery() {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-rule-profiles', session?.organizationId],
    queryFn: ({ signal }) => fetchPlayRuleProfiles(session!, signal),
    enabled: Boolean(session),
    staleTime: 30 * 60_000,
  });
}

export function usePlayTemplatesQuery() {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-templates', session?.organizationId],
    queryFn: ({ signal }) => fetchPlayTemplates(session!, signal),
    enabled: Boolean(session),
    staleTime: 5 * 60_000,
  });
}

export function usePlayVariantBatchesQuery(sourceDesignId?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-variant-batches', session?.organizationId, sourceDesignId],
    queryFn: ({ signal }) => fetchPlayVariantBatches(session!, sourceDesignId, signal),
    enabled: Boolean(session),
    staleTime: 20_000,
  });
}

export function usePlayVersionsQuery(designId?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-versions', session?.organizationId, designId],
    queryFn: ({ signal }) => fetchPlayVersions(session!, designId!, signal),
    enabled: Boolean(session && designId),
    staleTime: 10_000,
  });
}

export function usePlayVersionDiffQuery(designId?: string, baseSnapshotId?: string, compareSnapshotId?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-version-diff', session?.organizationId, designId, baseSnapshotId, compareSnapshotId],
    queryFn: ({ signal }) => fetchPlayVersionDiff(session!, designId!, baseSnapshotId!, compareSnapshotId!, signal),
    enabled: Boolean(session && designId && baseSnapshotId && compareSnapshotId && baseSnapshotId !== compareSnapshotId),
    staleTime: 30_000,
  });
}

export function usePlayLegalityQuery(designId?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-legality', session?.organizationId, designId],
    queryFn: ({ signal }) => fetchPlayLegality(session!, designId!, signal),
    enabled: Boolean(session && designId),
    staleTime: 10_000,
  });
}

export function usePlayDraftValidationQuery(design: PlayDesign, enabled = true, debounceMs = 350) {
  const { session } = useSession();
  const [debouncedDesign, setDebouncedDesign] = useState(design);

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedDesign(design), debounceMs);
    return () => window.clearTimeout(timeout);
  }, [debounceMs, design]);

  const fingerprint = compactFingerprint(debouncedDesign);
  return useQuery({
    queryKey: ['play-draft-validation', session?.organizationId, debouncedDesign.id, fingerprint],
    queryFn: ({ signal }) => validatePlayDesignDraft(session!, debouncedDesign, signal),
    enabled: Boolean(session && enabled),
    staleTime: 0,
    gcTime: 30_000,
    retry: 1,
  });
}

export function usePlayRoleViewQuery(designId: string | undefined, role: string, mode: 'player' | 'position_group' | 'coach', step?: number) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-role-view', session?.organizationId, designId, role, mode, step],
    queryFn: ({ signal }) => fetchPlayRoleView(session!, designId!, role, mode, step, signal),
    enabled: Boolean(session && designId && role),
    staleTime: 10_000,
  });
}

export function usePlayCommentsQuery(designId?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-comments', session?.organizationId, designId],
    queryFn: ({ signal }) => fetchPlayComments(session!, designId!, signal),
    enabled: Boolean(session && designId),
    staleTime: 5_000,
  });
}

export function usePlayPresenceQuery(designId?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ['play-presence', session?.organizationId, designId],
    queryFn: ({ signal }) => fetchPlayPresence(session!, designId!, signal),
    enabled: Boolean(session && designId),
    refetchInterval: 15_000,
  });
}

type PlayStreamStatus = 'disabled' | 'connecting' | 'live' | 'reconnecting' | 'offline';

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

export function usePlayDesignEventStream(designId?: string): { status: PlayStreamStatus; lastEvent?: PlayCollaborationEvent } {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<PlayStreamStatus>('disabled');
  const [lastEvent, setLastEvent] = useState<PlayCollaborationEvent>();

  useEffect(() => {
    if (!session || !designId) {
      setStatus('disabled');
      return undefined;
    }
    let cancelled = false;
    let sequence = 0;
    let connected = false;
    let controller: AbortController | undefined;
    const wait = (milliseconds: number) => new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds));
    const invalidateFor = (eventType: string) => {
      const organizationId = session.organizationId;
      if (eventType.includes('comment')) void queryClient.invalidateQueries({ queryKey: ['play-comments', organizationId, designId] });
      if (eventType.includes('presence')) void queryClient.invalidateQueries({ queryKey: ['play-presence', organizationId, designId] });
      if (['design_saved', 'branch_merged', 'design_published', 'design_rolled_back'].includes(eventType)) {
        void queryClient.invalidateQueries({ queryKey: ['play-designs', organizationId] });
        void queryClient.invalidateQueries({ queryKey: ['play-versions', organizationId, designId] });
        void queryClient.invalidateQueries({ queryKey: ['play-legality', organizationId, designId] });
      }
    };
    const consume = async () => {
      while (!cancelled) {
        setStatus(connected ? 'reconnecting' : 'connecting');
        controller = new AbortController();
        try {
          const response = await fetchPlayCollaborationStream(session, designId, sequence, controller.signal);
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
              if (parsed.event === 'stream_end') { ended = true; break; }
              const sequencing = acceptSequencedEvent(sequence, parsed.id);
              if (!sequencing.accepted) continue;
              sequence = sequencing.nextCursor;
              try {
                const event = JSON.parse(parsed.data) as PlayCollaborationEvent;
                setLastEvent(event);
                invalidateFor(event.event_type || parsed.event);
              } catch {
                // Ignore malformed event payloads; the stream will reconnect from its last valid sequence.
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
  }, [designId, queryClient, session?.organizationId, session?.token]);

  return { status, lastEvent };
}
