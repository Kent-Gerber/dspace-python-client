"""Advanced authentication example with session management."""

import asyncio
import getpass
from typing import Union, List
from rich.console import Console
from dspace_client import DSpaceAuthClient, DSpaceClient, ServerVersionMismatchError

console = Console()


def parse_target_versions(input_str: str) -> Union[str, List[str]]:
    """Parse target versions from user input."""
    input_str = input_str.strip()
    if not input_str:
        return "bleeding-edge"
    
    # Handle comma-separated list
    versions = [v.strip() for v in input_str.split(",") if v.strip()]
    if len(versions) == 1:
        return versions[0]
    return versions


async def main():
    """Demonstrate advanced authentication and session management."""
    
    # Prompt for target versions first
    target_input = console.input(
        "[bold cyan]Target DSpace versions[/bold cyan] [dim](comma-separated, e.g., 8.0,9.0 or press Enter for bleeding-edge):[/dim] "
    ).strip()
    target_versions = parse_target_versions(target_input)
    
    # Show supported versions in URL prompt
    if isinstance(target_versions, list):
        supported_str = ", ".join(target_versions)
    else:
        supported_str = target_versions
    
    # Interactive prompt for base URL with supported versions shown
    base_url = console.input(
        f"[bold cyan]DSpace base URL[/bold cyan] [dim](supported versions: {supported_str}, press Enter for https://demo.dspace.org):[/dim] "
    ).strip()
    
    if not base_url:
        base_url = "https://demo.dspace.org"
        console.print("[dim]→ Using default: https://demo.dspace.org[/dim]")
    
    # Auto-detect demo.dspace.org credentials
    base_url_normalized = base_url.rstrip("/").lower()
    is_demo = "demo.dspace.org" in base_url_normalized
    
    if is_demo:
        console.print("[dim]ℹ️  Using demo credentials: dspacedemo+admin@gmail.com[/dim]")
        username = "dspacedemo+admin@gmail.com"
        password = "dspace"
    else:
        username = console.input("[bold cyan]Admin username:[/bold cyan] ").strip()
        password = getpass.getpass("Admin password: ")
    
    # Create auth client
    auth = DSpaceAuthClient(base_url)
    
    # Check if server is reachable
    if not await auth.verify_server():
        print("❌ DSpace server is not reachable")
        return
    
    print("✅ DSpace server is reachable")
    
    # Authenticate
    try:
        jwt, status = await auth.authenticate(username, password)
        print(f"✅ Authentication successful")
        print(f"   JWT token: {jwt[:20]}...")
        print(f"   Authenticated: {status.get('authenticated', False)}")
        print(f"   User: {status.get('eperson', {}).get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Create client with version specification
    client = DSpaceClient(
        base_url=base_url,
        jwt_token=jwt,
        csrf_token=auth.csrf_token,
        http_client=auth.client,
        target_versions=target_versions,
    )
    
    # Verify server version (advanced example - can also use create_validated_client helper)
    try:
        await client.verify_server_version(raise_on_mismatch=True)
    except ServerVersionMismatchError as e:
        console.print(f"[red]Version mismatch:[/red] {e}")
        return
    
    # Check if session is still valid
    if await auth.is_session_valid():
        print("✅ Session is valid")
    else:
        print("❌ Session is invalid")
        return
    
    # Perform some operations
    try:
        # Create a test community
        community = await client.create_community("Advanced Auth Test")
        print(f"✅ Created community: {community['uuid']}")
        
        # Create a test collection
        collection = await client.create_collection(
            name="Advanced Auth Collection",
            parent_community_uuid=community["uuid"]
        )
        print(f"✅ Created collection: {collection['uuid']}")
        
        # Create a test item
        item = await client.create_item(
            name="Advanced Auth Item",
            owning_collection_uuid=collection["uuid"],
            metadata={
                "dc.title": [{"value": "Advanced Auth Item", "language": None, "authority": None, "confidence": -1}],
                "dc.description": [{"value": "Created with advanced authentication", "language": None, "authority": None, "confidence": -1}]
            }
        )
        print(f"✅ Created item: {item['uuid']}")
        
        # Clean up
        await client.delete_item(item["uuid"])
        await client.delete_collection(collection["uuid"])
        await client.delete_community(community["uuid"])
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
    
    # Check session validity again
    if await auth.is_session_valid():
        print("✅ Session is still valid after operations")
    else:
        print("❌ Session became invalid during operations")
    
    await auth.close()
    print("✅ Auth client closed")


if __name__ == "__main__":
    asyncio.run(main())
