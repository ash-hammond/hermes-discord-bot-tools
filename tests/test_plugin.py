import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import schemas  # noqa: E402
import tools  # noqa: E402


class PluginTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("DISCORD_BOT_TOKEN", None)
        os.environ.pop("DISCORD_BOT_TOOLS_ALLOW_DANGEROUS", None)

    def test_schemas_have_required_shape(self):
        for name in dir(schemas):
            if not name.startswith("DISCORD_"):
                continue
            schema = getattr(schemas, name)
            self.assertTrue(schema["name"].startswith("discord_"))
            self.assertIn("description", schema)
            self.assertEqual(schema["parameters"]["type"], "object")

    def test_missing_token_returns_json_error(self):
        os.environ.pop("DISCORD_BOT_TOKEN", None)
        result = json.loads(tools.discord_get_current_application({}))
        self.assertFalse(result["success"])
        self.assertIn("DISCORD_BOT_TOKEN", result["error"])

    def test_non_get_generic_requires_ack(self):
        os.environ["DISCORD_BOT_TOKEN"] = "fake.token.value"
        result = json.loads(tools.discord_api_request({
            "method": "PATCH",
            "path": "/applications/@me",
            "json_body": {"description": "x"},
        }))
        self.assertFalse(result["success"])
        self.assertIn("acknowledge_write_risk", result["error"])

    def test_generic_rejects_full_url(self):
        os.environ["DISCORD_BOT_TOKEN"] = "fake.token.value"
        result = json.loads(tools.discord_api_request({
            "method": "GET",
            "path": "https://discord.com/api/v10/users/@me",
        }))
        self.assertFalse(result["success"])
        self.assertIn("not a full URL", result["error"])

    def test_dangerous_generic_blocked_by_default(self):
        os.environ["DISCORD_BOT_TOKEN"] = "fake.token.value"
        os.environ.pop("DISCORD_BOT_TOOLS_ALLOW_DANGEROUS", None)
        result = json.loads(tools.discord_api_request({
            "method": "DELETE",
            "path": "/channels/1234567890",
            "acknowledge_write_risk": True,
        }))
        self.assertFalse(result["success"])
        self.assertIn("Blocked high-risk", result["error"])

    def test_register_wires_all_declared_tools(self):
        registered = []

        class Ctx:
            def register_tool(self, **kwargs):
                registered.append(kwargs)

        spec = importlib.util.spec_from_file_location("plugin_under_test", ROOT / "__init__.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        module.register(Ctx())
        names = {r["name"] for r in registered}
        self.assertIn("discord_api_request", names)
        self.assertIn("discord_update_application", names)
        self.assertEqual(len(names), 16)


if __name__ == "__main__":
    unittest.main()
