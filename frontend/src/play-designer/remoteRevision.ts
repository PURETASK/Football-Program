import type { EditorState } from './editorState';
import type { PlayDesign } from '../types';

export type RemoteRevisionDecision = 'ignore' | 'apply' | 'conflict';

/** Decide how an incoming server revision may affect the current editor. */
export function remoteRevisionDecision(state: Pick<EditorState, 'present' | 'dirty' | 'serverRevision'>, incoming: PlayDesign): RemoteRevisionDecision {
  if (incoming.id !== state.present.id) return 'ignore';
  const incomingRevision = Number(incoming._revision ?? 0);
  const localRevision = Number(state.serverRevision ?? state.present._revision ?? 0);
  if (!incomingRevision || incomingRevision <= localRevision) return 'ignore';
  return state.dirty ? 'conflict' : 'apply';
}

