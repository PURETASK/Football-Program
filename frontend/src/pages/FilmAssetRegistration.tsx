import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FileUp } from 'lucide-react';
import { type FormEvent } from 'react';

import { useSession } from '../auth/SessionContext';
import { MutationNotice } from '../components/OperationalWorkbench';
import { registerFilmAsset } from '../lib/api';
import { recordId, splitList } from '../lib/format';

export function FilmAssetRegistration() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (values: Parameters<typeof registerFilmAsset>[1]) => registerFilmAsset(session!, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['film-workspace', session?.organizationId] }),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    mutation.mutate({
      assetId: String(form.get('asset_id') || ''),
      filePath: String(form.get('file_path') || ''),
      durationSeconds: Number(form.get('duration_seconds') || 0),
      sourceKind: String(form.get('source_kind') || 'authorized_media'),
      sourceRef: String(form.get('source_ref') || ''),
      capturedAt: String(form.get('captured_at') || ''),
      teamContext: String(form.get('team_context') || ''),
      allowedRoots: splitList(String(form.get('allowed_roots') || '')),
    });
  }

  return (
    <form className="workbench-form workbench-pane" onSubmit={submit}>
      <div className="workbench-pane__header"><div><h3><FileUp aria-hidden="true" size={16} /> Register approved film asset</h3><p>Import a server-accessible media file into the organization-managed Film catalog. The file must already live under an approved source root.</p></div></div>
      <div className="workbench-form__grid">
        <label><span>Asset ID</span><input defaultValue={recordId('FILM-')} name="asset_id" pattern="FILM-.*" required /></label>
        <label><span>Duration seconds</span><input min="0.1" name="duration_seconds" required step="0.1" type="number" /></label>
        <label className="is-wide"><span>Server file path</span><input name="file_path" placeholder="C:\\approved-film\\week-01.mp4" required /></label>
        <label className="is-wide"><span>Approved source roots <small>comma separated</small></span><input name="allowed_roots" placeholder="C:\\approved-film" required /></label>
        <label><span>Source kind</span><select defaultValue="authorized_media" name="source_kind"><option>authorized_media</option><option>licensed_film</option><option>team_film</option><option>public_gamebook</option></select></label>
        <label><span>Source reference</span><input name="source_ref" placeholder="LICENSE-WK01-001" required /></label>
        <label><span>Captured at</span><input defaultValue={new Date().toISOString().slice(0, 10)} name="captured_at" required type="date" /></label>
        <label><span>Team context</span><input defaultValue="TEAM-DEMO-FIDOS" name="team_context" required /></label>
      </div>
      <div className="workbench-form__actions"><p className="workbench-form__hint">Registration records provenance, file hash, media type, and tenant scope. It never bypasses authorization or copies from an unapproved root.</p><button className="button button--primary" disabled={mutation.isPending || !session} type="submit"><FileUp size={15} /> Register asset</button></div>
      <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Film asset registered in the managed catalog." />
    </form>
  );
}
