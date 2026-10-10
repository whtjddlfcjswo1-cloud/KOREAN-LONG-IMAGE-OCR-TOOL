"""Integration tests for official LongImageOCR Model Context Protocol (MCP) Server.

Includes:
  1. Tool registration and execution via official MCPServer
  2. Multi-tile region inspection with global coordinate preservation (5,000px+ slice splitting into 3+ tiles)
  3. Real end-to-end MCP Client stdio subprocess transport test
"""

import os
import sys
import json
import asyncio
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from longocr.mcp_server import mcp_app


class TestMCPServerIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.test_dir, "test_mcp_image.png")
        self.tall_image_path = os.path.join(self.test_dir, "tall_mcp_image.png")

        # Create a small test image
        img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 20)
        except Exception:
            font = ImageFont.load_default()

        draw.text((20, 30), "MCP 테스트 문서", fill=(0, 0, 0), font=font)
        draw.text((20, 80), "삼성전자 NVDA +5.2%", fill=(0, 0, 0), font=font)
        draw.text((20, 150), "하단 정보 영역", fill=(0, 0, 0), font=font)
        img.save(self.image_path)

        # Create a tall 7000px image to test multi-tile region inspection
        tall_img = Image.new("RGB", (600, 7000), color=(255, 255, 255))
        draw_tall = ImageDraw.Draw(tall_img)
        for y in range(200, 6800, 400):
            draw_tall.text((40, y), f"글로벌 라인 y={y} — NVDA +1.5%", fill=(0, 0, 0), font=font)
        tall_img.save(self.tall_image_path)

    async def asyncTearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_mcp_list_tools(self):
        """Verifies that all 4 tools are registered with official MCP SDK."""
        self.assertIsNotNone(mcp_app, "mcp_app must be initialized")
        tools = await mcp_app.list_tools()
        tool_names = [t.name for t in tools]

        self.assertIn("long_image_ocr", tool_names)
        self.assertIn("read_ocr_output", tool_names)
        self.assertIn("inspect_ocr_region", tool_names)
        self.assertIn("ocr_status", tool_names)

    async def test_mcp_call_long_image_ocr_and_pagination(self):
        """Integration test calling long_image_ocr and read_ocr_output pagination."""
        out_dir = os.path.join(self.test_dir, "ocr_res")

        # 1. Call long_image_ocr
        call_res = await mcp_app.call_tool(
            "long_image_ocr",
            {
                "image_path": self.image_path,
                "mode": "fast",
                "output_dir": out_dir,
                "return_full_text": False
            }
        )
        self.assertFalse(call_res.is_error)
        text_content = call_res.content[0].text
        data = json.loads(text_content)

        self.assertIn("preview", data)
        self.assertIn("output_directory", data)
        self.assertIn("total_chars", data)
        self.assertNotIn("markdown", data, "markdown should be omitted by default to prevent context flood")

        # 2. Call read_ocr_output with pagination
        read_res = await mcp_app.call_tool(
            "read_ocr_output",
            {
                "output_dir": out_dir,
                "format": "markdown",
                "offset": 0,
                "limit": 50
            }
        )
        self.assertFalse(read_res.is_error)
        read_data = json.loads(read_res.content[0].text)

        self.assertEqual(read_data["offset"], 0)
        self.assertEqual(read_data["limit"], 50)
        self.assertIn("content", read_data)
        self.assertIn("total_chars", read_data)

    async def test_mcp_inspect_ocr_region_multi_tile_global_coordinates(self):
        """P1 Regression: 5,000px+ slice splitting into 3+ tiles must maintain correct global Y offsets."""
        y_start = 1000
        y_end = 6500  # 5,500px region -> will split into 3 tiles

        inspect_res = await mcp_app.call_tool(
            "inspect_ocr_region",
            {
                "image_path": self.tall_image_path,
                "y_start": y_start,
                "y_end": y_end,
                "language": "ko"
            }
        )
        self.assertFalse(inspect_res.is_error)
        res_data = json.loads(inspect_res.content[0].text)

        self.assertEqual(res_data["region"]["y_start"], y_start)
        self.assertEqual(res_data["region"]["y_end"], y_end)
        self.assertGreaterEqual(res_data["total_tiles_in_region"], 3, "5500px slice must split into at least 3 tiles")

        boxes = res_data["boxes"]
        self.assertGreater(len(boxes), 5)

        # Check that boxes span the entire 1000..6500 range without resetting to y_start
        min_y = min(min(pt[1] for pt in b["bbox_global"]) for b in boxes)
        max_y = max(max(pt[1] for pt in b["bbox_global"]) for b in boxes)

        self.assertGreaterEqual(min_y, y_start - 50, "Minimum box Y must be around y_start")
        self.assertGreater(max_y, 5000, "Maximum box Y must be deep into the crop (> 5000px), not reset to local coordinates")

    async def test_real_mcp_client_stdio_transport(self):
        """P1 Test: Real MCP Client connecting via stdio subprocess to longocr-mcp."""
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "longocr.mcp_server"],
            env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # List tools
                tools_res = await session.list_tools()
                tool_names = [t.name for t in tools_res.tools]
                self.assertIn("long_image_ocr", tool_names)
                self.assertIn("read_ocr_output", tool_names)
                self.assertIn("inspect_ocr_region", tool_names)
                self.assertIn("ocr_status", tool_names)

                # Call long_image_ocr over stdio transport
                out_dir = os.path.join(self.test_dir, "real_stdio_out")
                call_res = await session.call_tool(
                    "long_image_ocr",
                    {
                        "image_path": self.image_path,
                        "mode": "fast",
                        "output_dir": out_dir,
                        "return_full_text": False
                    }
                )
                self.assertFalse(call_res.is_error)
                data = json.loads(call_res.content[0].text)
                self.assertIn("preview", data)
                self.assertEqual(data["total_tiles"], 1)

                # Call read_ocr_output over stdio transport
                read_res = await session.call_tool(
                    "read_ocr_output",
                    {
                        "output_dir": out_dir,
                        "format": "markdown",
                        "offset": 0,
                        "limit": 100
                    }
                )
                self.assertFalse(read_res.is_error)
                read_data = json.loads(read_res.content[0].text)
                self.assertIn("content", read_data)

    def test_mcp_cli_help_and_version(self):
        """P0 Regression: Ensure longocr-mcp --help and --version exit cleanly with code 0 instead of hanging."""
        import subprocess
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent.parent))

        # Test --help
        p_help = subprocess.run(
            [sys.executable, "-m", "longocr.mcp_server", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        self.assertEqual(p_help.returncode, 0, f"--help failed with code {p_help.returncode}: {p_help.stderr}")
        self.assertIn("longocr-mcp", p_help.stdout)

        # Test --version
        p_ver = subprocess.run(
            [sys.executable, "-m", "longocr.mcp_server", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        self.assertEqual(p_ver.returncode, 0, f"--version failed with code {p_ver.returncode}: {p_ver.stderr}")
        self.assertIn("0.1.0a1", p_ver.stdout + p_ver.stderr)


if __name__ == "__main__":
    unittest.main()
