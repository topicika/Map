from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from cartographer.views import _graph_cache, load_all_graphs


class ViewIntegrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        load_all_graphs()
        self.dataset = "LE.json"
        self.graph = _graph_cache[self.dataset]
        node_ids = list(self.graph.get_id_to_index().keys())
        self.source = node_ids[0]
        self.goal = node_ids[1]

    def test_render_index_template(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search.html")

    def test_result_with_missing_fields(self):
        response = self.client.get(reverse("map_result"), {
            "sourceinput": "",
            "goalinput": "",
        })
        self.assertEqual(response.status_code, 302)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("nincs kitöltve" in message.message.lower() for message in messages))

    def test_result_with_success(self):
        response = self.client.get(reverse("map_result"), {
            "sourceinput": self.source,
            "goalinput": self.goal,
            "dataset": self.dataset,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "result.html")
        self.assertIn("path_json", response.context)
        self.assertIn("levels", response.context)
        self.assertTrue(len(response.context["path_json"]) >= 1)

    def test_result_with_invalid_ids(self):
        response = self.client.get(reverse("map_result"), {
            "sourceinput": "invalid",
            "goalinput": "invalid2",
            "dataset": self.dataset,
        })

        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("nem megfelelő" in message.message.lower() for message in messages))

    def test_search_with_unsupported_dataset(self):
        response = self.client.get(reverse("map_result"), {
            "sourceinput": self.source,
            "goalinput": self.goal,
            "dataset": "invalid.json",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "result.html")

    def test_result_without_path_found(self):
        response = self.client.get(reverse("map_result"), {
            "sourceinput": "LÉ-7-95-02-33",
            "goalinput": "LÉ--1-197-01-14",
            "dataset": self.dataset,
            "avoidstairs": "on",
            "useclosed": "",
        })

        if response.status_code == 302:
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any("nem létezik" in m.message.lower() for m in messages))

    def test_astar_returns_route(self):
        response = self.client.get(reverse("map_result"), {
            "sourceinput": self.source,
            "goalinput": self.goal,
            "dataset": self.dataset,
            "useastar": "on",
            "useclosed": "on",
            "avoidstairs": "on",
        })

        self.assertIn(response.status_code, (200, 302))
        self.assertTemplateUsed(response, "result.html")


    def test_search_without_text(self):
        response = self.client.get(reverse("search"), {"node": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"nodes": []})

    def test_search_returns_suggestions(self):
        substring = self.source[:3]

        response = self.client.get(reverse("search"), {
            "node": substring,
            "file": self.dataset,
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("nodes", data)
        self.assertTrue(len(data["nodes"]) > 0)

        first = data["nodes"][0]
        self.assertIn("identifier", first)

    def test_search_invalid_file(self):
        response = self.client.get(reverse("search"), {
            "node": "EF",
            "file": "missing.json",
        })

        self.assertEqual(response.status_code, 404)
        self.assertIn("Graph not found", response.content.decode())

    def test_help_view_renders(self):
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "help.html")
