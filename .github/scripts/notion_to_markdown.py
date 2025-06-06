import os
import glob
from ultimate_notion import Session
from ultimate_notion.config import Config
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]

# Set Notion token as environment variable that ultimate-notion expects
os.environ["NOTION_TOKEN"] = NOTION_TOKEN

# Create session and get database
session = Session()
database = session.get_db(NOTION_DATABASE_ID)

os.makedirs("_pages", exist_ok=True)

expected_files = set()
has_home_page = False


def create_file_content(title, type_val, content):
    """Generate Jekyll front matter and content"""
    front_matter = f"---\ntitle: {title}\nlayout: default\ntype: {type_val}"
    if type_val == "Home":
        front_matter += "\nnav_exclude: true"
    else:
        permalink = title.replace(' ', '_').lower()
        front_matter += f"\npermalink: /{permalink}/"
    return f"{front_matter}\n---\n\n{content}"

# Query all pages in the database
for page in database.query.execute():
    title = page.title or "Untitled"
    
    # Get the Type property safely using get_property
    type_val = ""
    try:
        type_prop = page.get_property('Type')
        if type_prop:
            type_val = type_prop.name if hasattr(type_prop, 'name') else str(type_prop)
    except:
        pass
    
    # Convert page content to markdown using ultimate-notion
    content = page.to_markdown()
    
    # Create appropriate file
    if type_val == "Home":
        file_path = os.path.join(os.path.dirname(__file__), '../../index.md')
        expected_files.add('index.md')
        has_home_page = True
    else:
        filename = f"{title.replace(' ', '_').lower()}.md"
        file_path = f"_pages/{filename}"
        expected_files.add(file_path)
    
    # Write file
    with open(file_path, "w") as f:
        f.write(create_file_content(title, type_val, content))
    
    print(f"Created: {file_path} ({type_val})")

# Clean up orphaned files
existing_files = set(glob.glob("_pages/*.md"))
for file_path in existing_files:
    if file_path not in expected_files:
        print(f"Removing: {file_path}")
        os.remove(file_path)

# Remove index.md if no Home page exists
if os.path.exists("index.md") and not has_home_page:
    print("Removing: index.md (no Home page)")
    os.remove("index.md")

print("Sync complete!")
