import { lazy, Suspense, useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { AlertTriangle, CircleHelp, LoaderCircle, Maximize2, Minus, Plus, ShieldCheck, Wifi, WifiOff } from 'lucide-react';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';

import { useSession } from '../auth/SessionContext';
import { BrandMark } from '../components/BrandMark';
import { SessionDialog } from '../components/SessionDialog';
import {
  usePlayAssetsQuery,
  usePlayCommentsQuery,
  usePlayDesignsQuery,
  usePlayDraftValidationQuery,
  usePlayLegalityQuery,
  usePlayRuleProfilesQuery,
  usePlayPresenceQuery,
  usePlayTemplatesQuery,
  usePlayVariantBatchesQuery,
  usePlayDesignEventStream,
  usePlayVersionDiffQuery,
  usePlayVersionsQuery,
} from '../hooks/useWorkspaceData';
import {
  ApiError,
  addPlayComment,
  branchPlayDesign,
  createPlayTemplate, createPlayVariants, requestPlayVariantBatchReview, approvePlayVariantBatchReview, createPlayVariantReleaseBundle, fetchPlayVariantReleaseBundle, fetchPlayTemplateLineageImpact, proposePlayTemplateLineageUpdate, approvePlayTemplateLineageUpdate,
  leavePlayPresence,
  mergePlayBranch,
  publishPlayDesign,
  approvePlayLegalityOverride,
  requestPlayLegalityOverride,
  requestPlayReview,
  savePlayDesign,
  updatePlayPresence,
} from '../lib/api';
import type { InspectorTab } from '../play-designer/DesignerInspector';
import { materializeAssetAction } from '../play-designer/actionMaterializer';
import { assetTool, createEditorState, createEmptyDesign, editorReducer, type EditorTool } from '../play-designer/editorState';
import { clamp } from '../play-designer/geometry';
import { remoteRevisionDecision } from '../play-designer/remoteRevision';
import { mergeRemoteDesign } from '../play-designer/remoteMerge';
import { clearOfflineDraft, readOfflineDraft, writeOfflineDraft, type OfflineDraftRecovery } from '../lib/offlineDraft';
import type { PlayAsset, PlayDesign, PlayElement, PlayMergeResult, PlayTemplate, Point } from '../types';
import '../styles/designer.css';

const DesignerExportDialog = lazy(() => import('../play-designer/DesignerExportDialog').then((module) => ({ default: module.DesignerExportDialog })));
const TeachingViewDialog = lazy(() => import('../play-designer/TeachingViewDialog').then((module) => ({ default: module.TeachingViewDialog })));
const DesignerTimeline = lazy(() => import('../play-designer/DesignerTimeline').then((module) => ({ default: module.DesignerTimeline })));
const DesignerTutorial = lazy(() => import('../play-designer/DesignerTutorial').then((module) => ({ default: module.DesignerTutorial })));
const AssetPalette = lazy(() => import('../play-designer/AssetPalette').then((module) => ({ default: module.AssetPalette })));
const DesignerInspector = lazy(() => import('../play-designer/DesignerInspector').then((module) => ({ default: module.DesignerInspector })));
const DesignerToolbar = lazy(() => import('../play-designer/DesignerToolbar').then((module) => ({ default: module.DesignerToolbar })));
const PlayDesignerCanvas = lazy(() => import('../play-designer/PlayDesignerCanvas').then((module) => ({ default: module.PlayDesignerCanvas })));
const TUTORIAL_TARGETS = ['toolbar', 'assets', 'inspector', 'canvas', 'toolbar', 'inspector', 'timeline', 'inspector', 'review', 'canvas'] as const;

function loadingWorkspace() {
  return (
    <div className="designer-route-state designer-route-state--loading">
      <BrandMark />
      <LoaderCircle className="spin" size={28} />
      <strong>Opening the play workspace</strong>
      <span>Loading the canonical design, asset registry, and staff state…</span>
    </div>
  );
}

function toolForAsset(asset: PlayAsset): EditorTool {
  if (['formation', 'front', 'coverage'].includes(asset.kind) && ['formation', 'front', 'coverage'].includes(asset.category ?? asset.kind)) return 'select';
  if (['read', 'landmark', 'check'].includes(asset.kind) || asset.category === 'teaching') return 'annotation';
  return assetTool(asset);
}

const PRESENCE_SESSION_KEY = 'nfl-fidos-play-designer-presence-v1';
const TUTORIAL_STORAGE_KEY = 'nfl-fidos-play-designer-tutorial-v1';

function createPresenceSessionId(): string {
  try {
    const existing = sessionStorage.getItem(PRESENCE_SESSION_KEY);
    if (existing) return existing;
    const generated = `PD-WEB-${crypto.randomUUID()}`;
    sessionStorage.setItem(PRESENCE_SESSION_KEY, generated);
    return generated;
  } catch {
    return `PD-WEB-${crypto.randomUUID()}`;
  }
}

function shouldStartTutorial(): boolean {
  try {
    return localStorage.getItem(TUTORIAL_STORAGE_KEY) !== 'complete';
  } catch {
    return true;
  }
}

function rememberTutorialCompletion(): void {
  try {
    localStorage.setItem(TUTORIAL_STORAGE_KEY, 'complete');
  } catch {
    // The tutorial still works when persistent browser storage is unavailable.
  }
}

function PlayDesignerWorkspace({ initialDesign, designs, templates }: { initialDesign: PlayDesign; designs: PlayDesign[]; templates: PlayTemplate[] }) {
  const { session } = useSession();
  const navigate = useNavigate();
  const routeLocation = useLocation();
  const queryClient = useQueryClient();
  const [state, dispatch] = useReducer(editorReducer, initialDesign, createEditorState);
  const assetsQuery = usePlayAssetsQuery(state.present);
  const variantBatchesQuery = usePlayVariantBatchesQuery(state.serverRevision ? state.present.id : undefined);
  const assets = assetsQuery.data ?? [];
  const [playbackTime, setPlaybackTime] = useState<number | null>(null);
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>('inspect');
  const [zoom, setZoom] = useState(1);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [saveMessage, setSaveMessage] = useState('');
  const [actionBusy, setActionBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState('');
  const [mergeConflict, setMergeConflict] = useState<PlayMergeResult | undefined>();
  const [conflict, setConflict] = useState<PlayDesign | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [teachingOpen, setTeachingOpen] = useState(false);
  const [offlineRecovery, setOfflineRecovery] = useState<OfflineDraftRecovery | null>(null);
  const [tutorialOpen, setTutorialOpen] = useState(shouldStartTutorial);
  const [tutorialIndex, setTutorialIndex] = useState(0);
  const [compareBaseId, setCompareBaseId] = useState('');
  const [compareSnapshotId, setCompareSnapshotId] = useState('');
  const [compareVisible, setCompareVisible] = useState(false);
  const canvasViewportRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<Point | undefined>(undefined);
  const remoteRevisionRef = useRef<number | undefined>(undefined);
  const savedDesignRef = useRef<PlayDesign>(initialDesign);
  const presenceSessionId = useMemo(createPresenceSessionId, []);
  const savedDesignId = state.serverRevision ? state.present.id : undefined;
  const versionsQuery = usePlayVersionsQuery(savedDesignId);
  const versionDiffQuery = usePlayVersionDiffQuery(savedDesignId, compareBaseId, compareSnapshotId);
  const legalityQuery = usePlayLegalityQuery(savedDesignId);
  const ruleProfilesQuery = usePlayRuleProfilesQuery();
  const draftValidationQuery = usePlayDraftValidationQuery(state.present);
  const commentsQuery = usePlayCommentsQuery(savedDesignId);
  const presenceQuery = usePlayPresenceQuery(savedDesignId);
  const collaborationStream = usePlayDesignEventStream(savedDesignId);
  const selectedElement = state.selected.length === 1 && state.selected[0].kind === 'element'
    ? (state.present.elements ?? []).find((element) => element.id === state.selected[0].id)
    : undefined;
  const activeValidation = draftValidationQuery.data ?? legalityQuery.data;
  const tutorialTarget = TUTORIAL_TARGETS[tutorialIndex] ?? 'toolbar';

  useEffect(() => {
    if (!session || !initialDesign.id) return undefined;
    let active = true;
    void readOfflineDraft(session, initialDesign.id).then((candidate) => {
      if (!active || !candidate) return;
      if (JSON.stringify(candidate.design) === JSON.stringify(initialDesign)) {
        clearOfflineDraft(session, initialDesign.id);
        return;
      }
      setOfflineRecovery(candidate);
    });
    return () => { active = false; };
  }, [initialDesign, session]);

  useEffect(() => {
    const snapshots = versionsQuery.data?.snapshots ?? [];
    if (snapshots.length < 2) return;
    setCompareBaseId((current) => current && snapshots.some((snapshot) => snapshot.id === current) ? current : snapshots[snapshots.length - 2].id);
    setCompareSnapshotId((current) => current && snapshots.some((snapshot) => snapshot.id === current) ? current : snapshots[snapshots.length - 1].id);
  }, [versionsQuery.data?.snapshots]);

  useEffect(() => {
    const event = collaborationStream.lastEvent;
    if (!event || !initialDesign._revision || event.actor === session?.subject) return;
    if (!['design_saved', 'branch_merged', 'design_published', 'design_rolled_back'].includes(event.event_type)) return;
    const revision = Number(initialDesign._revision);
    if (remoteRevisionRef.current === revision) return;
    const decision = remoteRevisionDecision(state, initialDesign);
    if (decision === 'conflict') {
      const merged = mergeRemoteDesign(savedDesignRef.current, state.present, initialDesign);
      if (merged.status === 'merged' && merged.design) {
        remoteRevisionRef.current = revision;
        savedDesignRef.current = initialDesign;
        dispatch({ type: 'recover_design', design: merged.design, baseDesign: initialDesign });
        setConflict(null);
        setSaveState('idle');
        setSaveMessage(`Staff revision ${initialDesign._revision} merged with your independent edits. Review and save.`);
        return;
      }
      remoteRevisionRef.current = revision;
      setConflict(initialDesign);
      setSaveState('error');
      setSaveMessage(`Staff revision ${initialDesign._revision} arrived. Review the remote change before saving.`);
    } else if (decision === 'apply') {
      remoteRevisionRef.current = revision;
      savedDesignRef.current = initialDesign;
      dispatch({ type: 'replace_design', design: initialDesign });
      setSaveState('saved');
      setSaveMessage(`Staff revision ${initialDesign._revision} applied from live collaboration.`);
    }
  }, [collaborationStream.lastEvent?.actor, collaborationStream.lastEvent?.event_type, collaborationStream.lastEvent?.id, initialDesign, session?.subject, state.dirty, state.present.id, state.serverRevision]);

  const closeTutorial = useCallback(() => setTutorialOpen(false), []);
  const openTutorial = useCallback(() => {
    setTutorialIndex(0);
    setInspectorTab('inspect');
    setTutorialOpen(true);
  }, []);
  const completeTutorial = useCallback(() => {
    rememberTutorialCompletion();
    setTutorialOpen(false);
  }, []);
  const changeTutorialStep = useCallback((index: number) => {
    const bounded = clamp(index, 0, TUTORIAL_TARGETS.length - 1);
    const target = TUTORIAL_TARGETS[bounded];
    if (target === 'review') setInspectorTab('review');
    if (target === 'inspector') setInspectorTab('inspect');
    setTutorialIndex(bounded);
  }, []);

  const refreshPlayData = useCallback(async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['play-designs', session?.organizationId] }),
      queryClient.invalidateQueries({ queryKey: ['play-versions', session?.organizationId, state.present.id] }),
      queryClient.invalidateQueries({ queryKey: ['play-legality', session?.organizationId, state.present.id] }),
    ]);
  }, [queryClient, session?.organizationId, state.present.id]);

  const saveCurrent = useCallback(async () => {
    if (!session || saveState === 'saving') return;
    setSaveState('saving');
    setSaveMessage('Saving an immutable server snapshot…');
    let offlineDraftSaved = false;
    try {
      // Complete the local recovery write before the network request. This
      // guarantees that an outage cannot win a race with draft preservation.
      offlineDraftSaved = await writeOfflineDraft(session, state.present);
    } catch {
      offlineDraftSaved = false;
    }
    try {
      const saved = await savePlayDesign(session, state.present, state.serverRevision);
      savedDesignRef.current = saved;
      dispatch({ type: 'mark_saved', design: saved });
      clearOfflineDraft(session, saved.id);
      setOfflineRecovery(null);
      setConflict(null);
      setSaveState('saved');
      setSaveMessage(`Revision ${saved._revision ?? 'new'} saved · v${saved.version ?? '0.1.0'}`);
      if (routeLocation.pathname.endsWith('/new')) navigate(`/playbook/designer/${encodeURIComponent(saved.id)}`, { replace: true });
      await refreshPlayData();
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 409) {
        const serverDesign = (failure.data as { server_design?: PlayDesign } | undefined)?.server_design;
        if (serverDesign) setConflict(serverDesign);
      }
      setSaveState('error');
      const recoveryMessage = offlineDraftSaved
        ? 'Draft preserved securely for retry.'
        : 'Offline draft preservation was unavailable; keep this window open and retry.';
      setSaveMessage(`${failure instanceof Error ? failure.message : 'The design could not be saved.'} ${recoveryMessage}`);
    }
  }, [navigate, refreshPlayData, routeLocation.pathname, saveState, session, state.present, state.serverRevision]);

  useEffect(() => {
    if (!state.dirty || saveState === 'saving' || conflict) return undefined;
    const timer = window.setTimeout(() => void saveCurrent(), 3000);
    return () => window.clearTimeout(timer);
  }, [conflict, saveCurrent, saveState, state.dirty]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!state.dirty) return;
      event.preventDefault();
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [state.dirty]);

  useEffect(() => {
    if (!session || !savedDesignId) return undefined;
    const heartbeat = () => void updatePlayPresence(session, savedDesignId, presenceSessionId, cursorRef.current).then(() => presenceQuery.refetch()).catch(() => undefined);
    heartbeat();
    const interval = window.setInterval(heartbeat, 20_000);
    return () => {
      window.clearInterval(interval);
      void leavePlayPresence(session, savedDesignId, presenceSessionId).catch(() => undefined);
    };
  }, [presenceSessionId, savedDesignId, session]);

  useEffect(() => {
    const hotkeys = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.matches('input, textarea, select, [contenteditable="true"]')) return;
      const command = event.metaKey || event.ctrlKey;
      if (command && event.key.toLowerCase() === 's') {
        event.preventDefault();
        void saveCurrent();
      } else if (command && event.key.toLowerCase() === 'z') {
        event.preventDefault();
        dispatch({ type: event.shiftKey ? 'redo' : 'undo' });
      } else if (command && event.key.toLowerCase() === 'y') {
        event.preventDefault();
        dispatch({ type: 'redo' });
      } else if (command && event.key.toLowerCase() === 'd') {
        event.preventDefault();
        dispatch({ type: 'duplicate_selected' });
      } else if (command && event.key.toLowerCase() === 'c') {
        event.preventDefault();
        dispatch({ type: 'copy_selected' });
      } else if (command && event.key.toLowerCase() === 'v') {
        event.preventDefault();
        dispatch({ type: 'paste_clipboard' });
      } else if (command && event.key.toLowerCase() === 'g') {
        event.preventDefault();
        dispatch({ type: 'group_selected', groupId: `GROUP-${Date.now().toString(36).toUpperCase()}` });
      } else if (event.key === 'Delete' || event.key === 'Backspace') {
        if (state.selected.length) {
          event.preventDefault();
          dispatch({ type: 'delete_selected' });
        }
      } else if (event.key === 'Escape') {
        dispatch({ type: 'set_tool', tool: 'select', asset: null });
        dispatch({ type: 'select', selection: null });
      } else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        if (!state.selected.length) return;
        event.preventDefault();
        const amount = event.shiftKey ? 5 : event.altKey ? 0.1 : state.snap ? 1 : 0.1;
        const delta = {
          x: event.key === 'ArrowLeft' ? -amount : event.key === 'ArrowRight' ? amount : 0,
          y: event.key === 'ArrowUp' ? -amount : event.key === 'ArrowDown' ? amount : 0,
        };
        dispatch({ type: 'nudge_selected', delta });
      }
    };
    window.addEventListener('keydown', hotkeys);
    return () => window.removeEventListener('keydown', hotkeys);
  }, [saveCurrent, state.selected, state.snap]);

  const chooseAsset = (asset: PlayAsset) => {
    if (asset.kind === 'formation') {
      dispatch({ type: 'apply_alignment', asset, patch: { formation: asset.term } });
      dispatch({ type: 'set_asset', asset });
      return;
    }
    if (asset.kind === 'front') {
      dispatch({ type: 'apply_alignment', asset, patch: { front: asset.term, formation: asset.term } });
      dispatch({ type: 'set_asset', asset });
      return;
    }
    if (asset.kind === 'coverage' && asset.category === 'coverage' && state.present.unit === 'defense') {
      dispatch({ type: 'update_meta', patch: { coverage: asset.term } });
    }
    dispatch({ type: 'set_tool', tool: toolForAsset(asset), asset });
  };

  const runAction = async <T,>(action: () => Promise<T>, success: (result: T) => void, message: string) => {
    setActionBusy(true);
    setActionMessage('');
    try {
      const result = await action();
      success(result);
      setActionMessage(message);
      await refreshPlayData();
    } catch (failure) {
      setActionMessage(failure instanceof Error ? failure.message : 'The controlled action failed.');
    } finally {
      setActionBusy(false);
    }
  };

  const requestReview = (decisionRef: string) => {
    if (!session) return;
    void runAction(
      () => requestPlayReview(session, state.present.id, decisionRef),
      (design) => dispatch({ type: 'mark_saved', design }),
      'Review requested. Publication remains human-controlled.',
    );
  };

  const publish = (decisionRef: string) => {
    if (!session) return;
    void runAction(
      () => publishPlayDesign(session, state.present.id, decisionRef),
      (design) => dispatch({ type: 'mark_saved', design }),
      'Immutable release published with its renderer and content checksums.',
    );
  };

  const branch = (branchId: string) => {
    if (!session) return;
    void runAction(
      () => branchPlayDesign(session, state.present.id, branchId),
      (design) => {
        savedDesignRef.current = design;
        dispatch({ type: 'replace_design', design });
        navigate(`/playbook/designer/${encodeURIComponent(design.id)}`);
      },
      `Branch ${branchId} created from the immutable base.`,
    );
  };

  const mergeBranch = (branchId: string) => {
    if (!session || !savedDesignId) return;
    void (async () => {
      setActionBusy(true);
      setActionMessage('');
      setMergeConflict(undefined);
      try {
        const result = await mergePlayBranch(session, savedDesignId, branchId, state.serverRevision);
        if (result.status === 'merged' && result.design) {
          dispatch({ type: 'mark_saved', design: result.design });
          setActionMessage(`Branch ${branchId} merged at ${result.merge_base_snapshot_id ?? 'the verified merge base'}.`);
          await refreshPlayData();
        } else {
          setMergeConflict(result);
          setActionMessage('Merge paused. Resolve the reported conflict paths before retrying.');
        }
      } catch (failure) {
        if (failure instanceof ApiError && failure.status === 409 && failure.data && typeof failure.data === 'object') {
          setMergeConflict(failure.data as PlayMergeResult);
          setActionMessage('Merge paused. The server returned an element-level conflict.');
        } else {
          setActionMessage(failure instanceof Error ? failure.message : 'The branch could not be merged.');
        }
      } finally {
        setActionBusy(false);
      }
    })();
  };

  const comment = async (text: string, elementId?: string) => {
    if (!session) return;
    setActionBusy(true);
    try {
      await addPlayComment(session, state.present.id, text, elementId);
      setActionMessage(elementId ? 'Comment linked to the selected assignment.' : 'Staff comment added.');
      await commentsQuery.refetch();
    } catch (failure) {
      setActionMessage(failure instanceof Error ? failure.message : 'Comment could not be saved.');
    } finally {
      setActionBusy(false);
    }
  };

  const requestLegalityOverride = (values: { issueCode: string; rationale: string; decisionRef: string; evidenceRefs: string[]; expiresAt: string }) => {
    if (!session) return;
    void runAction(
      () => requestPlayLegalityOverride(session, { designId: state.present.id, ...values, expiresAt: new Date(values.expiresAt).toISOString() }),
      () => undefined,
      `Owner review requested for ${values.issueCode}. The finding remains active until an authorized owner approves it.`,
    );
  };

  const approveLegalityOverride = (values: { overrideId: string; decisionRef: string }) => {
    if (!session) return;
    void runAction(
      () => approvePlayLegalityOverride(session, { designId: state.present.id, ...values }),
      () => undefined,
      `Legality override ${values.overrideId} approved. Re-run Checks before release.`,
    );
  };

  const saveConflictCopy = async () => {
    if (!session) return;
    const suffix = Date.now().toString(36).toUpperCase();
    const copy: PlayDesign = {
      ...state.present,
      id: `${state.present.id}-COPY-${suffix}`,
      name: `${state.present.name ?? state.present.concept ?? state.present.id} conflict copy`,
      status: 'draft',
      version: '0.1.0',
      _revision: undefined,
      parent_design_id: state.present.id,
    };
    setSaveState('saving');
    try {
      const saved = await savePlayDesign(session, copy);
      savedDesignRef.current = saved;
      dispatch({ type: 'replace_design', design: saved });
      setConflict(null);
      setSaveState('saved');
      navigate(`/playbook/designer/${encodeURIComponent(saved.id)}`, { replace: true });
      await refreshPlayData();
    } catch (failure) {
      setSaveState('error');
      setSaveMessage(failure instanceof Error ? failure.message : 'Conflict copy could not be saved.');
    }
  };

  const addMarker = (ms: number) => {
    const markers = [...(state.present.timeline?.markers ?? []), { id: `MARK-${Date.now().toString(36).toUpperCase()}`, label: 'Teaching marker', ms: Math.round(ms), kind: 'cue' }];
    dispatch({ type: 'update_meta', patch: { timeline: { ...state.present.timeline, markers } } });
  };

  const captureTemplate = async (input: { name: string; description: string; tags: string[]; elementIds?: string[]; parentTemplateId?: string }) => {
    if (!session || !state.present._revision) throw new Error('Save the play before capturing a reusable template.');
    await createPlayTemplate(session, { designId: state.present.id, ...input, templateKind: input.elementIds?.length ? 'custom' : 'complete_call', layer: input.elementIds?.length ? 'concept_layer' : 'complete_call' });
    await queryClient.invalidateQueries({ queryKey: ['play-templates', session.organizationId] });
    setActionMessage(`Template "${input.name}" captured from the immutable play snapshot.`);
  };

  const inspectTemplateLineage = async (templateId: string) => {
    if (!session) throw new Error('An authenticated organization session is required to inspect template lineage.');
    return fetchPlayTemplateLineageImpact(session, templateId);
  };

  const proposeTemplateLineage = async (input: { templateId: string; key: string; field: string; value: string }) => {
    if (!session) throw new Error('An authenticated organization session is required to propose a template change.');
    return proposePlayTemplateLineageUpdate(session, { templateId: input.templateId, patches: [{ key: input.key, patch: { [input.field]: input.value } }] });
  };

  const approveTemplateLineage = async (input: { proposalId: string; decisionRef: string }) => {
    if (!session) throw new Error('An authenticated organization session is required to approve a template change.');
    const result = await approvePlayTemplateLineageUpdate(session, input);
    await queryClient.invalidateQueries({ queryKey: ['play-templates', session.organizationId] });
    setActionMessage(`Template lineage proposal ${input.proposalId} applied. Affected active packages are now in review.`);
    return result;
  };

  const createVariants = async (input: { field: 'front' | 'coverage' | 'formation' | 'concept'; labels: string[]; assignmentPatches?: Array<{ element_id: string; patch: Record<string, unknown> }> }) => {
    if (!session) throw new Error('An authenticated organization session is required to generate variants.');
    const variants = input.labels.map((label) => ({ label, patch: { [input.field]: label.toLowerCase().replaceAll(' ', '_') }, ...(input.assignmentPatches?.length ? { assignment_patches: input.assignmentPatches } : {}) }));
    const report = await createPlayVariants(session, { designId: state.present.id, variants });
    setActionMessage(`${report.count} draft variants generated from ${state.present.name ?? state.present.id}. Each remains linked to the source play for review.`);
    await refreshPlayData();
    return report;
  };

  const requestVariantReview = async (batchId: string) => {
    if (!session) return;
    await requestPlayVariantBatchReview(session, batchId, `REVIEW-VARIANTS-${state.present.id}-${Date.now().toString(36).toUpperCase()}`);
    await queryClient.invalidateQueries({ queryKey: ['play-variant-batches', session.organizationId, state.present.id] });
    setActionMessage(`Variant batch ${batchId} is now under governed staff review.`);
  };

  const approveVariantReview = async (batchId: string) => {
    if (!session) return;
    await approvePlayVariantBatchReview(session, batchId, `APPROVE-VARIANTS-${state.present.id}-${Date.now().toString(36).toUpperCase()}`);
    await queryClient.invalidateQueries({ queryKey: ['play-variant-batches', session.organizationId, state.present.id] });
    setActionMessage(`Variant batch ${batchId} is approved for release; publish each child when ready.`);
  };

  const freezeVariantReleaseBundle = async (batchId: string) => {
    if (!session) return;
    await createPlayVariantReleaseBundle(session, batchId, `FREEZE-VARIANTS-${state.present.id}-${Date.now().toString(36).toUpperCase()}`);
    await queryClient.invalidateQueries({ queryKey: ['play-variant-batches', session.organizationId, state.present.id] });
    setActionMessage(`Variant batch ${batchId} is frozen into an immutable release manifest. Production activation remains disabled.`);
  };

  const inspectVariantReleaseBundle = async (bundleId: string) => {
    if (!session) throw new Error('An authenticated organization session is required to inspect a release bundle.');
    const result = await fetchPlayVariantReleaseBundle(session, bundleId);
    setActionMessage(result.integrity.valid ? `Release bundle ${bundleId} passed the server manifest integrity check.` : `Release bundle ${bundleId} failed the server manifest integrity check. Do not distribute it.`);
    return result.integrity;
  };

  const applyTemplate = (template: PlayTemplate, mode: 'replace' | 'layer') => {
    void import('../play-designer/templateMaterializer').then(({ applyPlayTemplate }) => {
      dispatch({ type: 'commit_design', design: applyPlayTemplate(state.present, template, mode) });
    }).catch(() => setActionMessage('The concept package could not be materialized. Your current play is unchanged.'));
  };

  const materializeAsset = (asset: PlayAsset) => {
    const selection = state.selected.length === 1 && state.selected[0].kind === 'player' ? state.selected[0] : undefined;
    const player = selection ? state.present.players?.find((item) => item.id === selection.id) : undefined;
    if (!player) {
      chooseAsset(asset);
      setActionMessage('Select one player icon first, or use the draw control to author this action manually.');
      return;
    }
    dispatch({ type: 'add_element', element: materializeAssetAction(state.present, player, asset) });
    dispatch({ type: 'set_tool', tool: 'select', asset: null });
    setActionMessage(`${asset.display_name ?? asset.term} starting action added for ${player.position ?? player.id}. Adjust its handles, timing, and coaching fields as needed.`);
  };

  return (
    <div className="play-designer-app" data-tutorial-target={tutorialOpen ? tutorialTarget : undefined}>
      <a className="skip-link" href="#designer-canvas">Skip to play canvas</a>
      <Suspense fallback={<div className="designer-component-loading" role="status">Loading editor controls…</div>}>
        <DesignerToolbar
          design={state.present}
          tool={state.tool}
          dirty={state.dirty}
          snap={state.snap}
          canUndo={Boolean(state.past.length)}
          canRedo={Boolean(state.future.length)}
          selectionCount={state.selected.length}
          hasClipboard={Boolean(state.clipboard)}
          saveState={saveState}
          presence={presenceQuery.data ?? []}
          onTool={(tool) => dispatch({ type: 'set_tool', tool, asset: tool === 'select' || tool === 'pan' ? null : undefined })}
          onSave={() => void saveCurrent()}
          onUndo={() => dispatch({ type: 'undo' })}
          onRedo={() => dispatch({ type: 'redo' })}
          onDuplicate={() => dispatch({ type: 'duplicate_selected' })}
          onCopy={() => dispatch({ type: 'copy_selected' })}
          onPaste={() => dispatch({ type: 'paste_clipboard' })}
          onMirror={() => dispatch({ type: 'mirror_selected' })}
          onGroup={() => dispatch({ type: 'group_selected', groupId: `GROUP-${Date.now().toString(36).toUpperCase()}` })}
          onDelete={() => dispatch({ type: 'delete_selected' })}
          onToggleSnap={() => dispatch({ type: 'toggle_snap' })}
          onRequestReview={() => setInspectorTab('review')}
          onExport={() => setExportOpen(true)}
          onTeaching={() => setTeachingOpen(true)}
          onTutorial={openTutorial}
        />
      </Suspense>

      <div className="designer-workspace">
        <Suspense fallback={<div className="designer-component-loading designer-component-loading--rail" role="status">Loading asset library…</div>}>
          <AssetPalette
            assets={assets}
            templates={templates}
            design={state.present}
            activeAsset={state.activeAsset}
            loading={assetsQuery.isPending}
            onChoose={chooseAsset}
            onApplyTemplate={applyTemplate}
            onSaveTemplate={captureTemplate}
            onCreateVariants={createVariants}
            variantBatches={variantBatchesQuery.data?.batches ?? []}
            onRequestVariantReview={requestVariantReview}
            onApproveVariantReview={session?.role === 'program_owner' ? approveVariantReview : undefined}
            onCreateVariantReleaseBundle={session?.role === 'program_owner' ? freezeVariantReleaseBundle : undefined}
            onInspectVariantReleaseBundle={inspectVariantReleaseBundle}
            onInspectLineage={inspectTemplateLineage}
            onProposeLineage={proposeTemplateLineage}
            onApproveLineage={session?.role === 'program_owner' ? approveTemplateLineage : undefined}
            canApproveLineage={session?.role === 'program_owner'}
            onOpenVariant={(designId) => navigate(`/playbook/designer/${encodeURIComponent(designId)}`)}
            selectedElementIds={state.selected.filter((selection): selection is { kind: 'element'; id: string } => selection.kind === 'element').map((selection) => selection.id)}
          />
        </Suspense>
        <main id="designer-canvas" className="designer-canvas-stage" data-tutorial="canvas">
          <div className="canvas-statusbar">
            <div>
              <span className="canvas-description-badge" title="Draw, select, position, and teach every canonical football object on the shared field."><CircleHelp size={12} /> Field canvas</span>
              <span className={`canvas-unit canvas-unit--${state.present.unit}`}>{state.present.unit}</span>
              <strong>{state.activeAsset?.display_name ?? (state.tool === 'select' ? 'Select and edit' : `${state.tool} tool`)}</strong>
              <span>{state.tool === 'select' ? 'Drag blank field to marquee · drag players or paths · arrow keys nudge' : state.tool === 'pan' ? 'Drag the field to pan · Ctrl/⌘ wheel to zoom' : 'Drag on the field to author the assignment'}</span>
            </div>
            <div className="canvas-statusbar__right">
              {saveMessage ? <span className={`save-message save-message--${saveState}`} role="status">{saveMessage}</span> : null}
              <span className="save-message save-message--saved" role="status">{collaborationStream.status === 'live' ? <Wifi size={13} /> : <WifiOff size={13} />} {collaborationStream.status === 'live' ? 'Live staff sync' : collaborationStream.status === 'offline' ? 'Staff sync reconnecting' : 'Staff sync connecting'}</span>
              <span><ShieldCheck size={13} /> {draftValidationQuery.isFetching ? 'checking draft' : activeValidation?.status ?? state.present.validation?.status ?? 'not checked'}</span>
            </div>
          </div>
          {conflict ? (
            <div className="designer-conflict" role="alert">
              <AlertTriangle size={19} />
              <div><strong>Another staff member saved this play.</strong><span>Choose the server revision or preserve your work as a separate branch-like copy.</span></div>
              <button type="button" onClick={() => { savedDesignRef.current = conflict; dispatch({ type: 'replace_design', design: conflict }); setConflict(null); setSaveState('idle'); }}>Load server</button>
              <button type="button" onClick={() => void saveConflictCopy()}>Save my copy</button>
            </div>
          ) : null}
          {offlineRecovery ? (
            <div className="designer-conflict" style={{ borderColor: 'rgb(255 209 102 / 0.42)', color: '#ffe3a1' }} role="status">
              <AlertTriangle size={19} />
              <div><strong>Secure offline draft found.</strong><span>Saved {new Date(offlineRecovery.updatedAt).toLocaleString()} · base revision {offlineRecovery.baseRevision ?? 'new'}.</span></div>
              <button type="button" onClick={() => { dispatch({ type: 'recover_design', design: offlineRecovery.design, baseDesign: initialDesign }); setOfflineRecovery(null); setSaveState('idle'); setSaveMessage('Recovered offline draft. It will sync when the organization API is available.'); }}>Recover draft</button>
              <button type="button" onClick={() => { clearOfflineDraft(session!, initialDesign.id); setOfflineRecovery(null); }}>Discard</button>
            </div>
          ) : null}
          <div ref={canvasViewportRef} className="canvas-viewport">
            <div className="canvas-zoom-layer" style={{ width: `${zoom * 100}%` }}>
              <Suspense fallback={<div className="designer-component-loading designer-component-loading--canvas" role="status">Loading field canvas…</div>}>
                <PlayDesignerCanvas
                  design={state.present}
                  compareDesign={compareVisible ? versionDiffQuery.data?.compare_design : undefined}
                  compareVisible={compareVisible}
                  selected={state.selected}
                  tool={state.tool}
                  activeAsset={state.activeAsset}
                  snap={state.snap}
                  playbackTime={playbackTime}
                  onSelect={(selection, additive) => dispatch({ type: 'select', selection, additive })}
                  onSelectMany={(selections, additive) => dispatch({ type: 'select_many', selections, additive })}
                  onMovePlayers={(ids, delta) => dispatch({ type: 'move_players', ids, delta })}
                  onMoveElements={(ids, delta) => dispatch({ type: 'move_elements', ids, delta })}
                  onAddElement={(element) => { dispatch({ type: 'add_element', element }); dispatch({ type: 'set_tool', tool: 'select' }); }}
                  onUpdateElement={(id, patch) => dispatch({ type: 'update_element', id, patch })}
                  onPan={(delta) => { canvasViewportRef.current?.scrollBy({ left: delta.x, top: delta.y }); }}
                  onZoom={(delta) => setZoom((value) => clamp(value + delta, 0.75, 1.8))}
                  onCursor={(point) => { cursorRef.current = point; }}
                  presence={presenceQuery.data ?? []}
                />
              </Suspense>
            </div>
            <div className="canvas-zoom-controls" aria-label="Canvas zoom controls">
              <button type="button" aria-label="Zoom out" onClick={() => setZoom((value) => clamp(value - 0.15, 0.75, 1.8))}><Minus size={15} /></button>
              <span>{Math.round(zoom * 100)}%</span>
              <button type="button" aria-label="Zoom in" onClick={() => setZoom((value) => clamp(value + 0.15, 0.75, 1.8))}><Plus size={15} /></button>
              <button type="button" aria-label="Fit field to workspace" onClick={() => setZoom(1)}><Maximize2 size={15} /></button>
            </div>
          </div>
          <Suspense fallback={<div className="timeline-loading"><LoaderCircle className="spin" size={16} /> Loading teaching timeline…</div>}>
            <DesignerTimeline
              design={state.present}
              selectedElement={selectedElement}
              playbackTime={playbackTime}
              onPlaybackTime={setPlaybackTime}
              onAddMarker={addMarker}
              onSelectElement={(id) => dispatch({ type: 'select', selection: { kind: 'element', id } })}
              onUpdateElement={(id, patch) => dispatch({ type: 'update_element', id, patch })}
              onUpdateTimeline={(timeline) => dispatch({ type: 'update_meta', patch: { timeline } })}
            />
          </Suspense>
        </main>
        <Suspense fallback={<div className="designer-component-loading designer-component-loading--rail" role="status">Loading assignment inspector…</div>}>
          <DesignerInspector
            design={state.present}
            selected={state.selected}
            tab={inspectorTab}
            dirty={state.dirty}
            legality={activeValidation}
            ruleProfiles={ruleProfilesQuery.data}
            validationPending={draftValidationQuery.isFetching}
            validationError={draftValidationQuery.error instanceof Error ? draftValidationQuery.error.message : undefined}
            versions={versionsQuery.data}
            versionDiff={versionDiffQuery.data}
            compareBaseId={compareBaseId}
            compareSnapshotId={compareSnapshotId}
            compareVisible={compareVisible}
            comments={commentsQuery.data ?? []}
            actionBusy={actionBusy}
            actionMessage={actionMessage}
            mergeConflict={mergeConflict}
            onTab={setInspectorTab}
            onSelect={(selection, additive) => dispatch({ type: 'select', selection, additive })}
            onSelectGroup={(groupId) => dispatch({ type: 'select_group', groupId })}
            onMeta={(patch) => dispatch({ type: 'update_meta', patch })}
            onFieldContext={(patch, translate) => dispatch({ type: 'apply_field_context', patch, translate })}
            onPlayer={(id, patch) => dispatch({ type: 'update_player', id, patch })}
            onElement={(id, patch) => dispatch({ type: 'update_element', id, patch })}
            onReorderElement={(id, direction) => dispatch({ type: 'reorder_element', id, direction })}
            assets={assets}
            templates={templates}
            onChooseAsset={chooseAsset}
            onApplyTemplate={applyTemplate}
            onMaterializeAsset={materializeAsset}
            onComment={(text, elementId) => void comment(text, elementId)}
            onRequestReview={requestReview}
            onPublish={publish}
            onBranch={branch}
            onCompare={(baseId, snapshotId) => { setCompareBaseId(baseId); setCompareSnapshotId(snapshotId); setCompareVisible(false); }}
            onToggleCompare={setCompareVisible}
            onMerge={mergeBranch}
            onRequestLegalityOverride={requestLegalityOverride}
            onApproveLegalityOverride={approveLegalityOverride}
            canApproveLegalityOverride={session?.role === 'program_owner'}
          />
        </Suspense>
      </div>
      {exportOpen ? (
        <Suspense fallback={<div className="designer-route-state designer-route-state--loading" role="status">Opening export workspace…</div>}>
          <DesignerExportDialog design={state.present} designs={designs} open onClose={() => setExportOpen(false)} />
        </Suspense>
      ) : null}
      {teachingOpen ? (
        <Suspense fallback={<div className="designer-route-state designer-route-state--loading" role="status">Opening teaching view…</div>}>
          <TeachingViewDialog design={state.present} open onClose={() => setTeachingOpen(false)} />
        </Suspense>
      ) : null}
      {tutorialOpen ? <Suspense fallback={null}><DesignerTutorial open stepIndex={tutorialIndex} onStep={changeTutorialStep} onClose={closeTutorial} onComplete={completeTutorial} /></Suspense> : null}
    </div>
  );
}

export function PlayDesignerPage() {
  const { session } = useSession();
  const { designId = 'new' } = useParams();
  const [searchParams] = useSearchParams();
  const [sessionOpen, setSessionOpen] = useState(false);
  const designsQuery = usePlayDesignsQuery();
  const templatesQuery = usePlayTemplatesQuery();
  const decodedId = decodeURIComponent(designId);
  const templateId = searchParams.get('template');
  const unitOverride = searchParams.get('unit') ?? undefined;
  const existing = designsQuery.data?.find((design) => design.id === decodedId);
  const template = templatesQuery.data?.find((item) => item.id === templateId);
  const newDesignRef = useRef<PlayDesign | undefined>(undefined);
  const [materializedTemplate, setMaterializedTemplate] = useState<PlayDesign | undefined>(undefined);
  if (decodedId === 'new' && !templateId && !newDesignRef.current) newDesignRef.current = createEmptyDesign(unitOverride);
  useEffect(() => {
    if (decodedId !== 'new' || !template) return undefined;
    let cancelled = false;
    setMaterializedTemplate(undefined);
    void import('../play-designer/templateMaterializer').then(({ applyPlayTemplate }) => {
      if (cancelled) return;
      const base = createEmptyDesign(unitOverride);
      const design = applyPlayTemplate(base, template, 'replace');
      newDesignRef.current = design;
      setMaterializedTemplate(design);
    });
    return () => { cancelled = true; };
  }, [decodedId, template?.id, unitOverride]);
  const selectedDesign = decodedId === 'new' ? (template ? materializedTemplate : newDesignRef.current) : existing;

  if (!session) {
    return (
      <div className="designer-route-state designer-route-state--gate">
        <BrandMark />
        <span className="designer-gate-icon"><WifiOff size={26} /></span>
        <p className="designer-kicker">Organization-scoped workspace</p>
        <h1>Connect the staff session.</h1>
        <p>The designer loads canonical plays, approvals, and asset rules only after an authorized team session is connected.</p>
        <button className="button button--electric" type="button" onClick={() => setSessionOpen(true)}>Connect organization</button>
        <SessionDialog open={sessionOpen} onClose={() => setSessionOpen(false)} />
      </div>
    );
  }

  if (designsQuery.isPending || templatesQuery.isPending || !selectedDesign) {
    if (!designsQuery.isPending && decodedId !== 'new' && !existing) {
      return <div className="designer-route-state"><BrandMark /><AlertTriangle size={26} /><h1>Play not found</h1><p>The requested design is not available to this organization.</p><Link className="button button--secondary" to="/playbook">Return to Playbook</Link></div>;
    }
    return loadingWorkspace();
  }

  return <PlayDesignerWorkspace key={selectedDesign.id} initialDesign={selectedDesign} designs={designsQuery.data ?? []} templates={templatesQuery.data ?? []} />;
}
