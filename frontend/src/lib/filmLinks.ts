import type { FilmLinkedRecordRef } from '../types';

export const FILM_LINK_TYPES = ['playbook', 'scouting', 'player_development', 'game_plan', 'analytics'] as const;

export function parseFilmLinkedRecordRefs(value: string): FilmLinkedRecordRef[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      const separator = item.indexOf(':');
      const recordType = (separator >= 0 ? item.slice(0, separator) : '').trim().toLowerCase();
      const recordId = (separator >= 0 ? item.slice(separator + 1) : item).trim();
      return { record_type: recordType, record_id: recordId, label: recordId };
    })
    .filter((item) => FILM_LINK_TYPES.includes(item.record_type as typeof FILM_LINK_TYPES[number]) && Boolean(item.record_id));
}

export function filmLinkPath(link: FilmLinkedRecordRef): string {
  const routes: Record<string, string> = {
    playbook: '/app/playbook',
    scouting: '/app/scouting',
    player_development: '/app/player',
    game_plan: '/app/game-plan',
    analytics: '/app/analytics',
  };
  const route = routes[link.record_type] || '/app';
  return `${route}?record=${encodeURIComponent(link.record_id)}&record_type=${encodeURIComponent(link.record_type)}`;
}
