import {
  ArrowLeft,
  Copy,
  ClipboardPaste,
  CircleHelp,
  Download,
  GraduationCap,
  GitBranch,
  Grid3X3,
  Hand,
  Link2,
  LockKeyhole,
  MousePointer2,
  Redo2,
  Save,
  Sparkles,
  Trash2,
  Undo2,
  Users,
  Wand2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import type { PlayDesign, PlayPresence } from '../types';
import { playDisplayName } from '../components/PlayCard';
import { StatusPill, statusTone } from '../components/StatusPill';
import type { EditorTool } from './editorState';

interface ToolbarProps {
  design: PlayDesign;
  tool: EditorTool;
  dirty: boolean;
  snap: boolean;
  canUndo: boolean;
  canRedo: boolean;
  selectionCount: number;
  hasClipboard?: boolean;
  saveState: 'idle' | 'saving' | 'saved' | 'error';
  presence: PlayPresence[];
  onTool: (tool: EditorTool) => void;
  onSave: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onDuplicate: () => void;
  onCopy: () => void;
  onPaste: () => void;
  onMirror: () => void;
  onGroup: () => void;
  onDelete: () => void;
  onToggleSnap: () => void;
  onRequestReview: () => void;
  onExport: () => void;
  onTeaching: () => void;
  onTutorial: () => void;
}

const PRIMARY_TOOLS: Array<{ tool: EditorTool; label: string; icon: typeof MousePointer2 }> = [
  { tool: 'select', label: 'Select', icon: MousePointer2 },
  { tool: 'pan', label: 'Pan', icon: Hand },
  { tool: 'route', label: 'Route', icon: Wand2 },
  { tool: 'motion', label: 'Motion', icon: Sparkles },
];

function saveLabel(state: ToolbarProps['saveState'], dirty: boolean): string {
  if (state === 'saving') return 'Saving…';
  if (state === 'error') return 'Retry save';
  if (dirty) return 'Save changes';
  return 'Saved';
}

export function DesignerToolbar({
  design,
  tool,
  dirty,
  snap,
  canUndo,
  canRedo,
  selectionCount,
  hasClipboard,
  saveState,
  presence,
  onTool,
  onSave,
  onUndo,
  onRedo,
  onDuplicate,
  onCopy,
  onPaste,
  onMirror,
  onGroup,
  onDelete,
  onToggleSnap,
  onRequestReview,
  onExport,
  onTeaching,
  onTutorial,
}: ToolbarProps) {
  return (
    <header className="designer-toolbar" data-tutorial="toolbar">
      <div className="designer-toolbar__identity">
        <Link className="designer-icon-button" to="/playbook" aria-label="Back to Playbook"><ArrowLeft size={19} /></Link>
        <div className="designer-toolbar__title">
          <div>
            <strong>{playDisplayName(design)}</strong>
            {dirty ? <span className="unsaved-dot" title="Unsaved changes" /> : null}
          </div>
          <span>{design.personnel || 'Open'} · {(design.formation ?? 'unassigned').replaceAll('_', ' ')} · v{design.version ?? '0.1.0'}</span>
        </div>
        <StatusPill label={(design.status ?? 'draft').replaceAll('_', ' ')} tone={statusTone(design.status)} />
      </div>

      <div className="designer-toolbar__tools" role="toolbar" aria-label="Canvas tools">
        {PRIMARY_TOOLS.map(({ tool: value, label, icon: Icon }) => (
          <button key={value} type="button" className={tool === value ? 'is-active' : ''} aria-pressed={tool === value} onClick={() => onTool(value)}>
            <Icon size={16} /><span>{label}</span>
          </button>
        ))}
        <span className="toolbar-divider" />
        <button type="button" disabled={!canUndo} aria-label="Undo" title="Undo (Ctrl+Z)" onClick={onUndo}><Undo2 size={16} /></button>
        <button type="button" disabled={!canRedo} aria-label="Redo" title="Redo (Ctrl+Shift+Z)" onClick={onRedo}><Redo2 size={16} /></button>
        <button type="button" disabled={!selectionCount} aria-label="Duplicate selection" title="Duplicate (Ctrl+D)" onClick={onDuplicate}><Copy size={16} /></button>
        <button type="button" disabled={!selectionCount} aria-label="Copy selection" title="Copy selection (Ctrl+C)" onClick={onCopy}><Copy size={16} /></button>
        <button type="button" disabled={hasClipboard === false} aria-label="Paste selection" title="Paste selection (Ctrl+V)" onClick={onPaste}><ClipboardPaste size={16} /></button>
        <button type="button" disabled={!selectionCount} aria-label="Mirror selection" title="Mirror selection" onClick={onMirror}><Link2 size={16} /></button>
        <button type="button" disabled={!selectionCount} aria-label="Group selection" title="Group selection (Ctrl+G)" onClick={onGroup}><Users size={16} /></button>
        <button type="button" disabled={!selectionCount} className="toolbar-danger" aria-label="Delete selection" title="Delete" onClick={onDelete}><Trash2 size={16} /></button>
        <span className="toolbar-divider" />
        <button type="button" className={snap ? 'is-active' : ''} aria-pressed={snap} title="Snap to one-yard grid" onClick={onToggleSnap}><Grid3X3 size={16} /><span>Snap</span></button>
      </div>

      <div className="designer-toolbar__actions">
        <div className="presence-stack" aria-label={`${presence.length} staff member${presence.length === 1 ? '' : 's'} present`}>
          {presence.slice(0, 3).map((person) => (
            <span key={person.session_id} title={`${person.display_name ?? person.subject ?? 'Staff'} is present`} style={{ '--presence-color': person.color ?? '#4cd6fa' } as React.CSSProperties}>
              {(person.display_name ?? person.subject ?? 'ST').slice(0, 2).toUpperCase()}
            </span>
          ))}
        </div>
        <button className="designer-action-button" type="button" aria-label="Open Play Designer tutorial" title="Open Play Designer tutorial" onClick={onTutorial}><CircleHelp size={16} /><span>Tutorial</span></button>
        <button className="designer-action-button" type="button" aria-label="Open teaching view" title="Open role-based teaching view" onClick={onTeaching}><GraduationCap size={16} /><span>Teach</span></button>
        <button className="designer-action-button" type="button" aria-label="Export play" title="Export play" onClick={onExport}><Download size={16} /><span>Export</span></button>
        <button className="designer-action-button" type="button" aria-label="Open review panel" title="Open review panel" onClick={onRequestReview}><GitBranch size={16} /><span>Review</span></button>
        <button
          className={`designer-save-button designer-save-button--${saveState}`}
          type="button"
          disabled={saveState === 'saving' || (!dirty && saveState !== 'error')}
          onClick={onSave}
        >
          {saveState === 'saving' ? <LockKeyhole size={16} /> : <Save size={16} />}
          <span>{saveLabel(saveState, dirty)}</span>
        </button>
      </div>
    </header>
  );
}
