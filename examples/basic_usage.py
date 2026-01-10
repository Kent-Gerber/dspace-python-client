"""Basic DSpace client usage example."""

import asyncio
import getpass
from typing import Union, List
from rich.console import Console
from dspace_client import create_validated_client, ServerVersionMismatchError

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
    """Demonstrate basic DSpace client usage."""
    
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
    
    # Default to demo.dspace.org if user just pressed Enter
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
    
    # Authenticate and create client with automatic version validation
    try:
        auth, client = await create_validated_client(
            base_url=base_url,
            username=username,
            password=password,
            target_versions=target_versions,
        )
        # Version validation happens automatically - if major version mismatch,
        # ServerVersionMismatchError would have been raised
    except ServerVersionMismatchError as e:
        console.print(f"[red]Version mismatch:[/red] {e}")
        return
    # On first run, this will fetch REST API docs from GitHub
    # Subsequent runs use cached docs
    
    # Create a community (validated against target versions)
    community = await client.create_community("My Community")
    print(f"Created: {community['uuid']}")
    
    # Create a collection in the community
    collection = await client.create_collection(
        name="My Collection",
        parent_community_uuid=community["uuid"]
    )
    print(f"Created collection: {collection['uuid']}")
    
    # Create an item in the collection
    item = await client.create_item(
        name="My Item",
        owning_collection_uuid=collection["uuid"],
        metadata={
            "dc.title": [{"value": "My Item", "language": None, "authority": None, "confidence": -1}],
            "dc.description": [{"value": "A sample item", "language": None, "authority": None, "confidence": -1}]
        }
    )
    print(f"Created item: {item['uuid']}")
    
    # Create a bundle and upload a bitstream
    bundle = await client.create_bundle(item["uuid"], "ORIGINAL")
    print(f"Created bundle: {bundle['uuid']}")
    
    # Upload a sample bitstream
    sample_content = b"This is sample content for the bitstream."
    bitstream = await client.upload_bitstream(
        bundle_uuid=bundle["uuid"],
        filename="sample.txt",
        content=sample_content,
        metadata={
            "dc.title": [{"value": "Sample File", "language": None, "authority": None, "confidence": -1}]
        }
    )
    print(f"Uploaded bitstream: {bitstream['uuid']}")
    
    # Clean up (optional)
    # await client.delete_item(item['uuid'])
    # await client.delete_collection(collection['uuid'])
    # await client.delete_community(community['uuid'])
    
    await auth.close()


if __name__ == "__main__":
    asyncio.run(main())
