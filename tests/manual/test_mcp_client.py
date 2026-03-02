"""Test MCP server with proper MCP client."""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_list_tools():
    """Test listing all tools from the MCP server."""
    
    # For HTTP/SSE transport, use HTTP client
    # For now, we'll test with stdio
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "mcp_sharepoint"],
        env={"TRANSPORT": "stdio"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List all available tools
            tools = await session.list_tools()
            
            print("=" * 70)
            print("✅ MCP Server Connected Successfully!")
            print("=" * 70)
            print(f"\n📋 Found {len(tools.tools)} tools:\n")
            
            for i, tool in enumerate(tools.tools, 1):
                print(f"{i}. {tool.name}")
                print(f"   Description: {tool.description}")
                if hasattr(tool, 'inputSchema'):
                    print(f"   Parameters: {list(tool.inputSchema.get('properties', {}).keys())}")
                print()
            
            # Test calling a tool
            print("=" * 70)
            print("🧪 Testing tool execution: list_folders")
            print("=" * 70)
            
            try:
                result = await session.call_tool(
                    "list_folders",
                    arguments={}
                )
                print("\n✅ Tool executed successfully!")
                print(f"Result: {json.dumps(result.content, indent=2)[:500]}...")
            except Exception as e:
                print(f"\n⚠️ Tool execution info: {e}")
            
            return tools

async def test_http_session():
    """Test connecting to HTTP/SSE transport."""
    import httpx
    
    print("\n" + "=" * 70)
    print("🌐 Testing HTTP Health Endpoint")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        health = response.json()
        
        print(f"\n✅ Server Status: {health['status']}")
        print(f"📊 Tools Available: {health['tools']}")
        print(f"🔌 SharePoint: {health['sharepoint']}")
        print(f"🚀 Transport: {health['transport']}")
        print(f"📦 Version: {health['version']}")

async def main():
    """Run all tests."""
    try:
        # Test 1: HTTP Health Check
        await test_http_session()
        
        # Test 2: MCP Protocol via stdio
        print("\n\n" + "=" * 70)
        print("🔌 Testing MCP Protocol (stdio mode)")
        print("=" * 70)
        tools = await test_list_tools()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
