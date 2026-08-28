import { useId } from 'react';

import type { PlayDesign, PlayElement, Point } from '../types';

const YARD_LINES = [10, 20, 30, 40, 50, 60, 70, 80, 90];
const HASH_LINES = [19, 34];

function elementPoints(element: PlayElement): Point[] {
  return element.points ?? element.path ?? [];
}

function pathData(points: Point[]): string {
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
}

export function FieldThumbnail({ design, name }: { design: PlayDesign; name: string }) {
  const markerId = `arrow-${useId().replace(/:/g, '')}`;
  const routeElements = (design.elements ?? []).filter((element) => elementPoints(element).length > 1).slice(0, 8);
  const routeColor = design.unit === 'defense' ? '#ffb547' : '#63d8ff';

  return (
    <svg className="field-thumbnail" viewBox="0 0 100 53" role="img" aria-label={`${name} ${design.unit} field diagram`}>
      <title>{`${name} ${design.unit} field diagram`}</title>
      <defs>
        <linearGradient id={`${markerId}-field`} x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#123e36" />
          <stop offset="1" stopColor="#092d29" />
        </linearGradient>
        <marker id={markerId} markerHeight="4" markerWidth="4" orient="auto" refX="3.5" refY="2">
          <path d="M0,0 L4,2 L0,4 Z" fill={routeColor} />
        </marker>
      </defs>
      <rect width="100" height="53" rx="4" fill={`url(#${markerId}-field)`} />
      {YARD_LINES.map((x) => (
        <line key={x} x1={x} x2={x} y1="0" y2="53" stroke="rgba(255,255,255,.14)" strokeWidth=".35" />
      ))}
      {HASH_LINES.map((y) => (
        <line key={y} x1="0" x2="100" y1={y} y2={y} stroke="rgba(255,255,255,.1)" strokeDasharray="1 2" strokeWidth=".4" />
      ))}
      <line x1="0" x2="100" y1="26.5" y2="26.5" stroke="rgba(255,255,255,.48)" strokeWidth=".55" />
      {routeElements.map((element) => (
        <path
          key={element.id}
          d={pathData(elementPoints(element))}
          fill="none"
          markerEnd={`url(#${markerId})`}
          stroke={routeColor}
          strokeDasharray={element.kind === 'motion' ? '2 1.2' : undefined}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.05"
        />
      ))}
      {(design.players ?? []).map((player) =>
        player.start ? (
          <g key={player.id}>
            <circle
              cx={player.start.x}
              cy={player.start.y}
              fill={design.unit === 'defense' ? '#ffb547' : '#f5f8ff'}
              r="1.7"
              stroke="#07111f"
              strokeWidth=".45"
            />
          </g>
        ) : null,
      )}
    </svg>
  );
}
