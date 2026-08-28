import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Bell,
  BarChart3,
  BookOpenText,
  Bot,
  CalendarClock,
  ChevronDown,
  ClipboardList,
  MessageCircle,
  Film,
  Home,
  Menu,
  Search,
  Settings2,
  ShieldCheck,
  Target,
  UsersRound,
  X,
  type LucideIcon,
} from 'lucide-react';
import { Link, NavLink, Outlet } from 'react-router-dom';

import { useSession } from '../auth/SessionContext';
import { useOperatorSummaryQuery } from '../hooks/useWorkspaceData';
import { BrandMark } from './BrandMark';
import { CommandPalette } from './CommandPalette';
import { SessionDialog } from './SessionDialog';
import { StatusPill, statusTone } from './StatusPill';

interface NavigationItem {
  label: string;
  path: string;
  section: string;
  icon: LucideIcon;
  ownerOnly?: boolean;
  playerOnly?: boolean;
}

const NAVIGATION: NavigationItem[] = [
  { label: 'Today', path: '/', section: 'today', icon: Home },
  { label: 'Operations Inbox', path: '/inbox', section: 'inbox', icon: Bell },
  { label: 'Roster & Personnel', path: '/roster', section: 'roster', icon: UsersRound },
  { label: 'Outcome Analytics', path: '/analytics', section: 'analytics', icon: BarChart3 },
  { label: 'Delivery Center', path: '/delivery', section: 'delivery', icon: CalendarClock },
  { label: 'Collaboration', path: '/collaboration', section: 'collaboration', icon: MessageCircle },
  { label: 'Playbook', path: '/playbook', section: 'playbook', icon: BookOpenText },
  { label: 'Film Room', path: '/film', section: 'film', icon: Film },
  { label: 'Practice', path: '/practice', section: 'practice', icon: CalendarClock },
  { label: 'Scouting', path: '/scouting', section: 'scouting', icon: Target },
  { label: 'Game Plan', path: '/game-plan', section: 'game_plan', icon: ClipboardList },
  { label: 'Player', path: '/player', section: 'player', icon: UsersRound, playerOnly: true },
  { label: 'Admin', path: '/admin', section: 'governance', icon: Settings2, ownerOnly: true },
];

function roleLabel(role?: string): string {
  if (!role) return 'Guest workspace';
  return role.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function AppShell() {
  const { session } = useSession();
  const summaryQuery = useOperatorSummaryQuery();
  const [menuOpen, setMenuOpen] = useState(false);
  const [sessionOpen, setSessionOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const closeSession = useCallback(() => setSessionOpen(false), []);
  const closeCommand = useCallback(() => setCommandOpen(false), []);
  const summary = summaryQuery.data;

  const navigation = useMemo(() => {
    const allowed = new Set(summary?.allowed_sections ?? []);
    return NAVIGATION.filter((item) => {
      if (item.ownerOnly && session?.role !== 'program_owner') return false;
      if (item.playerOnly && session?.role !== 'player') return false;
      if (!session || allowed.size === 0) return !item.ownerOnly && !item.playerOnly;
      return allowed.has(item.section) || item.section === 'today';
    });
  }, [session, summary?.allowed_sections]);

  useEffect(() => {
    const handleCommandShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCommandOpen(true);
      }
    };
    window.addEventListener('keydown', handleCommandShortcut);
    return () => window.removeEventListener('keydown', handleCommandShortcut);
  }, []);

  return (
    <div className="app-frame">
      <a className="skip-link" href="#app-content">Skip to main content</a>
      <aside className={menuOpen ? 'sidebar sidebar--open' : 'sidebar'} aria-label="Primary navigation">
        <div className="sidebar__top">
          <BrandMark />
          <button className="icon-button sidebar__close" type="button" aria-label="Close navigation" onClick={() => setMenuOpen(false)}>
            <X size={19} />
          </button>
        </div>

        <nav className="sidebar__navigation" aria-label="Primary workspaces">
          <p className="sidebar__label">Command center</p>
          {navigation.map(({ label, path, icon: Icon }) => (
            <NavLink
              className={({ isActive }) => (isActive ? 'nav-item nav-item--active' : 'nav-item')}
              end={path === '/'}
              key={path}
              onClick={() => setMenuOpen(false)}
              to={path}
            >
              <Icon aria-hidden="true" size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__intelligence">
          <div className="sidebar__intelligence-icon" aria-hidden="true">
            <Bot size={19} />
          </div>
          <div>
            <strong>Football intelligence</strong>
            <span>Evidence-linked · human controlled</span>
          </div>
        </div>

        <button className="sidebar__account" type="button" onClick={() => setSessionOpen(true)}>
          <span className="avatar">{session?.subject?.slice(0, 2).toUpperCase() || 'FT'}</span>
          <span>
            <strong>{session?.subject || 'Connect team'}</strong>
            <small>{roleLabel(session?.role)}</small>
          </span>
          <ChevronDown aria-hidden="true" size={16} />
        </button>
      </aside>

      {menuOpen ? <button className="sidebar-scrim" type="button" aria-label="Close navigation" onClick={() => setMenuOpen(false)} /> : null}

      <div className="app-stage">
        <header className="topbar">
          <div className="topbar__left">
            <button className="icon-button topbar__menu" type="button" aria-label="Open navigation" onClick={() => setMenuOpen(true)}>
              <Menu size={20} />
            </button>
            <div className="topbar__season">
              <span>2026 program</span>
              {summary ? <StatusPill label={summary.stage} tone={statusTone(summary.organization_population?.status)} /> : null}
            </div>
          </div>
          <div className="topbar__actions">
            <button className="command-search" type="button" aria-label="Open command search" onClick={() => setCommandOpen(true)}>
              <Search size={17} />
              <span>Search plays, clips, people…</span>
              <kbd>⌘ K</kbd>
            </button>
            <Link className="icon-button notification-button" to="/inbox" aria-label={`${summary?.pending_review_count ?? 0} pending reviews and operational alerts`}>
              <Bell size={19} />
              {summary?.pending_review_count ? <span>{summary.pending_review_count}</span> : null}
            </Link>
            <button className={session ? 'connection-chip connection-chip--active' : 'connection-chip'} type="button" onClick={() => setSessionOpen(true)}>
              <ShieldCheck size={16} />
              <span>{session ? session.organizationId : 'Connect team'}</span>
            </button>
          </div>
        </header>

        <main id="app-content" className="app-content">
          <Outlet />
        </main>
      </div>
      <CommandPalette open={commandOpen} onClose={closeCommand} navigation={navigation} />
      <SessionDialog open={sessionOpen} onClose={closeSession} />
    </div>
  );
}
