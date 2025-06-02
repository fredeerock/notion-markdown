import os
import glob
from notion_client import Client
from markdownify import markdownify as md
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]

notion = Client(auth=NOTION_TOKEN)

# Query the database
results = notion.databases.query(database_id=NOTION_DATABASE_ID)["results"]

os.makedirs("_pages", exist_ok=True)

# Track which files should exist after processing
expected_files = set()
has_home_page = False

for page in results:
    props = page["properties"]
    title = props["Title"]["title"][0]["plain_text"] if props["Title"]["title"] else "Untitled"
    
    # Safely get the Type property with proper null checking
    type_prop = props.get("Type", {})
    if type_prop and type_prop.get("select"):
        type_val = type_prop["select"].get("name", "")
    else:
        type_val = ""
    
    page_id = page["id"]
    blocks = notion.blocks.children.list(block_id=page_id)["results"]

    def block_to_md(block):
        block_type = block["type"]
        if block_type == "paragraph" and "rich_text" in block[block_type]:
            return "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "heading_1" and "rich_text" in block[block_type]:
            return "# " + "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "heading_2" and "rich_text" in block[block_type]:
            return "## " + "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "heading_3" and "rich_text" in block[block_type]:
            return "### " + "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "bulleted_list_item" and "rich_text" in block[block_type]:
            return "- " + "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "numbered_list_item" and "rich_text" in block[block_type]:
            return "1. " + "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "to_do" and "rich_text" in block[block_type]:
            checked = block[block_type].get("checked", False)
            box = "[x]" if checked else "[ ]"
            return f"- {box} " + "".join([t.get("plain_text", "") for t in block[block_type]["rich_text"]])
        elif block_type == "image" and block[block_type].get("external"):
            url = block[block_type]["external"]["url"]
            return f"![]({url})"
        return ""

    content = "\n\n".join([block_to_md(block) for block in blocks if block_to_md(block)])
    
    # Home page logic
    if type_val == "Home":
        out_path = os.path.join(os.path.dirname(__file__), '../../index.md')
        expected_files.add('index.md')
        has_home_page = True
        with open(out_path, "w") as f:
            f.write(f"---\ntitle: {title}\nlayout: default\ntype: {type_val}\n---\n\n{content}")
    else:
        filename = f"{title.replace(' ', '_').lower()}.md"
        permalink_name = title.replace(' ', '_').lower()
        expected_files.add(f'_pages/{filename}')
        with open(f"_pages/{filename}", "w") as f:
            f.write(f"---\ntitle: {title}\nlayout: default\ntype: {type_val}\npermalink: /{permalink_name}/\n---\n\n{content}")
    print(f"Processing: {title}")
    print(f"Blocks: {blocks}")
    print(f"Generated content for {title}:\n{content}")

# Clean up orphaned files
print("\n--- Cleaning up orphaned files ---")

# Get all existing markdown files
existing_page_files = set(glob.glob("_pages/*.md"))
index_exists = os.path.exists("index.md")

# Remove orphaned files in _pages/
for existing_file in existing_page_files:
    if existing_file not in expected_files:
        print(f"Removing orphaned file: {existing_file}")
        os.remove(existing_file)

# Handle index.md - remove if no Home page exists in Notion
if index_exists and not has_home_page:
    print("Removing orphaned index.md (no Home page in Notion)")
    os.remove("index.md")

print(f"Expected files: {expected_files}")
print(f"Processing complete!")
