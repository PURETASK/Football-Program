export interface CoverageShellBox {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

const BOXES: Record<string, CoverageShellBox> = {
  deep_left: { id: 'deep_left', label: 'Deep left', x: 1, y: 1, width: 32, height: 14 },
  deep_middle: { id: 'deep_middle', label: 'Deep middle', x: 34, y: 1, width: 32, height: 14 },
  deep_right: { id: 'deep_right', label: 'Deep right', x: 67, y: 1, width: 32, height: 14 },
  deep_half_left: { id: 'deep_half_left', label: 'Deep half left', x: 1, y: 1, width: 48, height: 14 },
  deep_half_right: { id: 'deep_half_right', label: 'Deep half right', x: 51, y: 1, width: 48, height: 14 },
  flat_left: { id: 'flat_left', label: 'Flat left', x: 1, y: 15.5, width: 25, height: 12 },
  flat_right: { id: 'flat_right', label: 'Flat right', x: 74, y: 15.5, width: 25, height: 12 },
  hook_curl_left: { id: 'hook_curl_left', label: 'Hook/curl left', x: 20, y: 15.5, width: 28, height: 12 },
  hook_curl_middle: { id: 'hook_curl_middle', label: 'Hook/curl middle', x: 36, y: 15.5, width: 28, height: 12 },
  hook_curl_right: { id: 'hook_curl_right', label: 'Hook/curl right', x: 52, y: 15.5, width: 28, height: 12 },
  robber: { id: 'robber', label: 'Robber / low hole', x: 38, y: 27.5, width: 24, height: 12 },
  bracket: { id: 'bracket', label: 'Bracket / double', x: 26, y: 8, width: 48, height: 28 },
  man: { id: 'man', label: 'Man coverage', x: 1, y: 1, width: 98, height: 38 },
};

export const COVERAGE_SHELL_OPTIONS = Object.values(BOXES);

export function coverageShellBoxes(zones: string[] | undefined): CoverageShellBox[] {
  const seen = new Set<string>();
  return (zones ?? []).map((zone) => BOXES[zone]).filter((box): box is CoverageShellBox => {
    if (!box || seen.has(box.id)) return false;
    seen.add(box.id);
    return true;
  });
}
