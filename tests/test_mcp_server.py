#!/usr/bin/env python3
"""
Simple test script for MCP BigQuery Server
"""

import asyncio
import json
import sys
from typing import Any


class MCPTester:
    def __init__(self):
        self.process = None
        self.request_id = 0

    def get_next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    async def send_request(self, method: str, params: Any = None) -> dict:
        """Send a JSON-RPC request to the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": self.get_next_id(),
            "method": method,
        }
        if params is not None:
            request["params"] = params

        request_json = json.dumps(request) + "\n"
        print(f"→ Sending: {method}")

        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")

        response = json.loads(response_line.decode().strip())
        print(f"← Received: {response.get('result', response.get('error', 'Unknown'))}")
        return response

    async def test_server(self):
        """Test the MCP server functionality."""
        try:
            # Start the server process
            print("🚀 Starting MCP BigQuery Server...")
            self.process = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                "python",
                "src/mcp_bigquery_server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait a moment for server to start
            await asyncio.sleep(1)

            print("\n📋 Testing MCP Protocol...")

            # 1. Initialize
            init_response = await self.send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                    "clientInfo": {"name": "mcp-tester", "version": "1.0.0"},
                },
            )

            if "error" in init_response:
                print(f"❌ Initialization failed: {init_response['error']}")
                return False

            print("✅ Server initialized successfully!")
            server_info = init_response["result"]["serverInfo"]
            print(f"   Server: {server_info['name']} v{server_info['version']}")

            # 2. Send initialized notification
            await self.send_initialized_notification()

            # 3. List tools
            tools_response = await self.send_request("tools/list", {})
            if "error" in tools_response:
                print(f"❌ Tools list failed: {tools_response['error']}")
                return False

            tools = tools_response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   • {tool['name']}: {tool['description']}")

            # 4. Test a simple tool (validate_query)
            print("\n🔧 Testing query validation tool...")
            validate_response = await self.send_request(
                "tools/call", {"name": "validate_query", "arguments": {"query": "SELECT 1 as test"}}
            )

            if "error" in validate_response:
                print(f"❌ Tool call failed: {validate_response['error']}")
                return False

            print("✅ Query validation tool works!")
            print(f"   Result: {validate_response['result']['content'][0]['text']}")

            print("\n🎉 All tests passed! MCP server is working correctly.")
            return True

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False

        finally:
            if self.process:
                self.process.terminate()
                await self.process.wait()

    async def send_initialized_notification(self):
        """Send the initialized notification."""
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json.encode())
        await self.process.stdin.drain()


async def main():
    """Main test function."""
    print("🧪 MCP BigQuery Server Test Suite")
    print("=" * 40)

    tester = MCPTester()
    success = await tester.test_server()

    if success:
        print("\n✅ Server is ready for use!")
        sys.exit(0)
    else:
        print("\n❌ Server has issues.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
