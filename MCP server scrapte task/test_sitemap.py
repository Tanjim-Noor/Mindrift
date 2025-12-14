"""Test sitemap content extraction."""
import requests
import re

r = requests.get('https://mcp.so/sitemap_projects_5.xml', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
content = r.text

print(f'Status: {r.status_code}')
print(f'Content length: {len(content)}')
print()

# Try different patterns
patterns = [
    (r'href="(/server/[^"]+)"', 'href server relative'),
    (r'href="(https://mcp\.so/server/[^"]+)"', 'href server absolute'),
    (r'/server/([^/"<>\s]+)/([^/"<>\s]+)', 'server/name/author pattern'),
    (r'https://mcp\.so/project/([^"<>\s]+)', 'project URLs'),
    (r'https://mcp\.so/([^"<>\s]+)', 'all mcp.so URLs'),
]

for pattern, name in patterns:
    matches = re.findall(pattern, content)
    print(f'{name}: {len(matches)} matches')
    if matches and len(matches) > 0:
        print(f'  Samples: {matches[:5]}')
    print()

# Also check if it contains /project/ URLs instead of /server/
if '/project/' in content:
    print('Contains /project/ URLs!')
    project_urls = re.findall(r'https://mcp\.so/project/[^"<>\s]+', content)
    print(f'  Found {len(project_urls)} project URLs')
    if project_urls:
        print(f'  Samples: {project_urls[:5]}')
