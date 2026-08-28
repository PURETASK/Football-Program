import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.http_server import create_server
from nfl_fidos.play_design_collaboration import PlayDesignCollaborationService
from nfl_fidos.tenant_repository import TenantRepository
from tests.test_play_creation import design


class HttpServerTests(unittest.TestCase):
    def test_health_and_router_are_reachable_over_http(self):
        with tempfile.TemporaryDirectory() as directory:
            server, repository = create_server(port=0, database_path=Path(directory) / "http.sqlite3")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}"
                with urlopen(base + "/health") as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("application/json", response.headers["Content-Type"])
                    self.assertEqual(json.loads(response.read())["status"], "ok")
                with urlopen(base + "/v1/control") as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.loads(response.read())["data"]["stage"], "STAGE-0")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()

    def test_malformed_json_is_a_structured_400(self):
        with tempfile.TemporaryDirectory() as directory:
            server, repository = create_server(port=0, database_path=Path(directory) / "http.sqlite3")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                request = Request(f"http://127.0.0.1:{server.server_address[1]}/v1/plays/compile", data=b"not-json", method="POST", headers={"Content-Type":"application/json", "Content-Length":"8"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code, 400)
                self.assertEqual(json.loads(error.exception.read())["status"], "error")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()

    def test_legacy_ui_assets_are_served_with_browser_safe_media_types(self):
        with tempfile.TemporaryDirectory() as directory:
            server, repository = create_server(port=0, database_path=Path(directory) / "http.sqlite3")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}"
                expected = {
                    "/play-designer.js": "text/javascript",
                    "/play-designer.css": "text/css",
                    "/play-designer-interactive.js": "text/javascript",
                    "/pilot-verification.css": "text/css",
                }
                for path, media_type in expected.items():
                    with self.subTest(path=path), urlopen(base + path) as response:
                        self.assertEqual(response.status, 200)
                        self.assertIn(media_type, response.headers["Content-Type"])
                        self.assertGreater(len(response.read()), 100)
                        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()

    def test_unknown_legacy_ui_asset_is_a_structured_404(self):
        with tempfile.TemporaryDirectory() as directory:
            server, repository = create_server(port=0, database_path=Path(directory) / "http.sqlite3")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}"
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/play-designer-does-not-exist.js")
                self.assertEqual(error.exception.code, 404)
                self.assertEqual(json.loads(error.exception.read())["error"], "UI asset not found")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()

    def test_react_app_and_spa_fallback_serve_built_assets(self):
        index_path = Path(__file__).parents[1] / "frontend" / "dist" / "index.html"
        self.assertTrue(index_path.is_file(), "Run npm run build from frontend/ before the Python integration suite")
        with tempfile.TemporaryDirectory() as directory:
            server, repository = create_server(port=0, database_path=Path(directory) / "http.sqlite3")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}"
                with urlopen(base + "/app") as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("text/html", response.headers["Content-Type"])
                    document = response.read().decode("utf-8")
                    self.assertIn('<div id="root"></div>', document)
                    self.assertIn("script-src 'self'", response.headers["Content-Security-Policy"])
                deep_links = (
                    "/app/playbook",
                    "/app/inbox",
                    "/app/roster",
                    "/app/analytics",
                    "/app/delivery",
                    "/app/playbook/designer/PD-DIRECT-REFRESH",
                    "/app/film",
                    "/app/practice",
                    "/app/scouting",
                    "/app/game-plan",
                    "/app/player",
                    "/app/admin",
                    "/app/reviews",
                )
                for deep_link in deep_links:
                    with self.subTest(deep_link=deep_link), urlopen(base + deep_link) as response:
                        self.assertEqual(response.status, 200)
                        self.assertIn('<div id="root"></div>', response.read().decode("utf-8"))
                asset_paths = re.findall(r'(?:src|href)="(/app/assets/[^"]+)"', document)
                self.assertGreaterEqual(len(asset_paths), 2)
                for asset_path in asset_paths:
                    with self.subTest(asset=asset_path), urlopen(base + asset_path) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.headers["Cache-Control"], "public, max-age=31536000, immutable")
                        suffix = Path(asset_path).suffix
                        if suffix == ".js":
                            self.assertIn("text/javascript", response.headers["Content-Type"])
                            self.assertIn("charset=utf-8", response.headers["Content-Type"])
                        elif suffix == ".css":
                            self.assertIn("text/css", response.headers["Content-Type"])
                            self.assertIn("charset=utf-8", response.headers["Content-Type"])
                        self.assertGreater(len(response.read()), 100)
                designer_chunks = list((index_path.parent / "assets").glob("PlayDesignerPage-*.js"))
                self.assertEqual(len(designer_chunks), 1, "The full-screen designer must compile to one lazy-loaded route chunk")
                self.assertLess(designer_chunks[0].stat().st_size, 90 * 1024, "Keep the designer route chunk below the local 90 KiB transfer budget")
                workspace_chunk_names = ("OperationsInboxPage", "RosterPage", "AnalyticsPage", "DeliveryPage", "FilmPage", "PracticePage", "ScoutingPage", "GamePlanPage", "PlayerPage", "AdminPage", "ReviewsPage")
                workspace_chunks = []
                for chunk_name in workspace_chunk_names:
                    chunks = list((index_path.parent / "assets").glob(f"{chunk_name}-*.js"))
                    self.assertEqual(len(chunks), 1, f"{chunk_name} must compile to its own lazy-loaded route chunk")
                    self.assertLess(chunks[0].stat().st_size, 30 * 1024, f"Keep {chunk_name} below the local 30 KiB transfer budget")
                    workspace_chunks.extend(chunks)
                main_chunks = [index_path.parent / asset_path.removeprefix("/app/") for asset_path in asset_paths if asset_path.endswith(".js")]
                style_chunks = [index_path.parent / asset_path.removeprefix("/app/") for asset_path in asset_paths if asset_path.endswith(".css")]
                self.assertTrue(main_chunks and style_chunks)
                self.assertLess(max(path.stat().st_size for path in main_chunks), 350 * 1024, "Keep the migrated shell JavaScript below the local 350 KiB budget")
                self.assertLess(max(path.stat().st_size for path in style_chunks), 90 * 1024, "Keep the combined visual system CSS below the local 90 KiB budget")
                with urlopen(base + "/app/assets/" + designer_chunks[0].name) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("text/javascript", response.headers["Content-Type"])
                    self.assertIn("charset=utf-8", response.headers["Content-Type"])
                    self.assertGreater(len(response.read()), 100)
                for workspace_chunk in workspace_chunks:
                    with self.subTest(workspace_chunk=workspace_chunk.name), urlopen(base + "/app/assets/" + workspace_chunk.name) as response:
                        self.assertEqual(response.status, 200)
                        self.assertIn("text/javascript", response.headers["Content-Type"])
                        self.assertIn("charset=utf-8", response.headers["Content-Type"])
                        self.assertGreater(len(response.read()), 100)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()

    def test_play_designer_collaboration_stream_is_authenticated_and_replayable(self):
        secret = "http-collaboration-stream-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        token = issue_token(subject="COACH-STREAM", role="coach_staff", organization_id="ORG-STREAM", secret=secret)
        temporary = tempfile.TemporaryDirectory()
        server, repository = create_server(port=0, database_path=Path(temporary.name) / "http.sqlite3")
        try:
            created_status, created = handle_request(
                method="POST",
                path="/v1/playbook/designs",
                headers={"Authorization": "Bearer " + token},
                body={"organization_id": "ORG-STREAM", "design": design()},
                service=server.fidos_service,
            )
            self.assertEqual(created_status, 201)
            design_id = created["data"]["id"]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_address[1]}/v1/playbook/designs/{design_id}/events/stream?organization_id=ORG-STREAM&since=0&timeout=2"
                request = Request(url, headers={"Authorization": "Bearer " + token, "Accept": "text/event-stream"})
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("text/event-stream", response.headers["Content-Type"])
                    self.assertEqual(response.headers["X-Frame-Options"], "DENY")
                    self.assertEqual(response.readline().decode("utf-8"), "retry: 1500\n")
                    self.assertEqual(response.readline().decode("utf-8"), "\n")
                    self.assertTrue(response.readline().decode("utf-8").startswith("id: 1"))
            finally:
                server.shutdown()
                thread.join(timeout=3)
        finally:
            server.server_close()
            repository.close()
            temporary.cleanup()
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_two_authenticated_play_clients_replay_shared_events_after_reconnect(self):
        secret = "http-two-client-collaboration-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach_token = issue_token(subject="COACH-TWO-CLIENT", role="coach_staff", organization_id="ORG-TWO-CLIENT", secret=secret)
        owner_token = issue_token(subject="OWNER-TWO-CLIENT", role="program_owner", organization_id="ORG-TWO-CLIENT", secret=secret)
        temporary = tempfile.TemporaryDirectory()
        server, repository = create_server(port=0, database_path=Path(temporary.name) / "http.sqlite3")
        try:
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers={"Authorization": "Bearer " + coach_token}, body={"organization_id": "ORG-TWO-CLIENT", "design": design()}, service=server.fidos_service)
            self.assertEqual(created_status, 201)
            design_id = created["data"]["id"]
            collaboration = PlayDesignCollaborationService(TenantRepository(server.fidos_service.repository, organization_id="ORG-TWO-CLIENT", actor="COACH-TWO-CLIENT"))
            first = collaboration.events(design_id=design_id)[0]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}/v1/playbook/designs/{design_id}/events/stream?organization_id=ORG-TWO-CLIENT&since=0&timeout=1"
                received_sequences = []
                for token in (coach_token, owner_token):
                    request = Request(base, headers={"Authorization": "Bearer " + token, "Accept": "text/event-stream"})
                    with urlopen(request, timeout=3) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.readline().decode("utf-8"), "retry: 1500\n")
                        self.assertEqual(response.readline().decode("utf-8"), "\n")
                        event_id = response.readline().decode("utf-8")
                        self.assertEqual(event_id, "id: 1\n")
                        received_sequences.append(int(event_id.removeprefix("id: ").strip()))
                second = collaboration.record_event(design_id=design_id, event_type="comment_added", actor="OWNER-TWO-CLIENT", payload={"comment_id": "COMMENT-TWO-CLIENT"}, idempotency_key="TWO-CLIENT-2")
                self.assertEqual(first["sequence"], 1)
                self.assertEqual(second["sequence"], 2)
                replay_url = f"http://127.0.0.1:{server.server_address[1]}/v1/playbook/designs/{design_id}/events/stream?organization_id=ORG-TWO-CLIENT&since=1&timeout=1"
                request = Request(replay_url, headers={"Authorization": "Bearer " + coach_token, "Accept": "text/event-stream"})
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.readline().decode("utf-8"), "retry: 1500\n")
                    self.assertEqual(response.readline().decode("utf-8"), "\n")
                    self.assertEqual(response.readline().decode("utf-8"), "id: 2\n")
                self.assertEqual(received_sequences, [1, 1])
            finally:
                server.shutdown()
                thread.join(timeout=3)
        finally:
            server.server_close()
            repository.close()
            temporary.cleanup()
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_organization_collaboration_stream_is_authenticated_and_replayable(self):
        secret = "http-org-collaboration-stream-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        token = issue_token(subject="OWNER-ORG-STREAM", role="program_owner", organization_id="ORG-ORG-STREAM", secret=secret)
        temporary = tempfile.TemporaryDirectory()
        server, repository = create_server(port=0, database_path=Path(temporary.name) / "http.sqlite3")
        try:
            created_status, _ = handle_request(
                method="POST",
                path="/v1/collaboration/threads",
                headers={"Authorization": "Bearer " + token},
                body={"organization_id": "ORG-ORG-STREAM", "thread_id": "COLLAB-THREAD-STREAM", "title": "Stream review", "body": "Review this decision.", "entity_type": "game_plan", "entity_id": "GAMEPLAN-STREAM"},
                service=server.fidos_service,
            )
            self.assertEqual(created_status, 201)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_address[1]}/v1/collaboration/events/stream?organization_id=ORG-ORG-STREAM&since=0&timeout=2"
                request = Request(url, headers={"Authorization": "Bearer " + token, "Accept": "text/event-stream"})
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("text/event-stream", response.headers["Content-Type"])
                    self.assertEqual(response.readline().decode("utf-8"), "retry: 1500\n")
                    self.assertEqual(response.readline().decode("utf-8"), "\n")
                    self.assertTrue(response.readline().decode("utf-8").startswith("id: 1"))
            finally:
                server.shutdown()
                thread.join(timeout=3)
        finally:
            server.server_close()
            repository.close()
            temporary.cleanup()
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
