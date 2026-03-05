import os, requests
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT")
h = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
repo = 'Arunaah/autonomous-engineer'
prs = requests.get(f'https://api.github.com/repos/{repo}/pulls?state=open', headers=h).json()
for pr in prs:
    if pr['title'].startswith('[AE]'):
        num = pr['number']
        r = requests.patch(f'https://api.github.com/repos/{repo}/pulls/{num}',
                           headers=h, json={'state': 'closed'})
        print('Closed PR', num, '->', r.status_code)
print('Done')
