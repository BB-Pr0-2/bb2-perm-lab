#!/usr/bin/env python3
"""Create objects AUTHORED BY github-actions[bot] in the lab repo (fixtures for author-privilege tests)."""
import base64, json, os, urllib.request, urllib.error
T = os.environ['GH_TOKEN']
FX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures.json')))
LAB = 'BB-Pr0-2/bb2-perm-lab'
def call(m, u, b=None):
    url = u if u.startswith('http') else 'https://api.github.com' + u
    h = {'Authorization': 'Bearer ' + T, 'Accept': 'application/vnd.github+json', 'User-Agent': 'seed-bot', 'X-GitHub-Api-Version': '2022-11-28'}
    d = json.dumps(b).encode() if b is not None else None
    if d: h['Content-Type'] = 'application/json'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, d, h, method=m), timeout=40) as r:
            return r.status, json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode('utf-8', 'replace')
def gql(q, v):
    return call('POST', '/graphql', {'query': q, 'variables': v})
out = {}
def rec(k, st, j, keep):
    out[k] = {'status': st}
    if isinstance(j, dict):
        for kk in keep:
            out[k][kk] = j.get(kk)
    else:
        out[k]['err'] = j
    print(k, st, out[k])
T4 = FX['issues']['lab_T4']['number']
for k in ['BOT_I', 'BOT_I_CTRL']:
    st, j = call('POST', f'/repos/{LAB}/issues', {'title': f'{k} authored by github-actions[bot]', 'body': 'seeded by GITHUB_TOKEN'})
    rec(k, st, j, ['number', 'id', 'node_id'])
for k in ['BOT_C', 'BOT_C_DEL', 'BOT_C_CTRL', 'BOT_C_CTRL_DEL']:
    st, j = call('POST', f'/repos/{LAB}/issues/{T4}/comments', {'body': f'{k} comment authored by github-actions[bot]'})
    rec(k, st, j, ['id', 'node_id'])
cats = FX['disc_categories']['bb2-perm-lab']
for k in ['BOT_D', 'BOT_D_CTRL']:
    st, j = gql('mutation($r:ID!,$c:ID!,$t:String!){ createDiscussion(input:{repositoryId:$r, categoryId:$c, title:$t, body:"seeded"}){ discussion{ id number } } }',
                {'r': FX['bb2-perm-lab']['node_id'], 'c': cats['Q&A']['id'], 't': f'{k} discussion authored by github-actions[bot]'})
    d = (j.get('data') or {}).get('createDiscussion') if isinstance(j, dict) else None
    out[k] = {'status': st, **(d['discussion'] if d else {'err': str(j)[:300]})}; print(k, out[k])
    if d:
        st2, j2 = gql('mutation($d:ID!){ addDiscussionComment(input:{discussionId:$d, body:"bot comment on bot discussion"}){ comment{ id databaseId } } }', {'d': d['discussion']['id']})
        dc = (j2.get('data') or {}).get('addDiscussionComment') if isinstance(j2, dict) else None
        out[k + 'C'] = dc['comment'] if dc else {'err': str(j2)[:300]}; print(k + 'C', out[k + 'C'])
# bot branch + PR
st, j = call('GET', f'/repos/{LAB}/git/ref/heads/main'); main_sha = j['object']['sha']
for k in ['BOT_PR', 'BOT_PR_CTRL']:
    br = 'bot-src-' + k.lower().replace('_', '-')
    st, j = call('POST', f'/repos/{LAB}/git/refs', {'ref': 'refs/heads/' + br, 'sha': main_sha}); print('ref', br, st)
    st, j = call('PUT', f'/repos/{LAB}/contents/{br}.txt', {'message': f'{k} file', 'content': base64.b64encode(b'bot\n').decode(), 'branch': br}); print('file', st)
    st, j = call('POST', f'/repos/{LAB}/pulls', {'title': f'{k} PR authored by github-actions[bot]', 'head': br, 'base': 'main', 'body': 'seeded'})
    rec(k, st, j, ['number', 'id', 'node_id'])
st, j = call('POST', f'/repos/{LAB}/commits/{main_sha}/comments', {'body': 'BOT_CC commit comment authored by github-actions[bot]'})
rec('BOT_CC', st, j, ['id', 'node_id'])
pra = FX.get('lab_PR_A')
if pra:
    st, j = call('POST', f"/repos/{LAB}/pulls/{pra['number']}/comments", {'body': 'BOT_RC review comment by github-actions[bot]', 'commit_id': pra['head_sha'], 'path': 'pr-a.txt', 'line': 1, 'side': 'RIGHT'})
    rec('BOT_RC', st, j, ['id', 'node_id'])
st, j = call('POST', f'/repos/{LAB}/releases', {'tag_name': 'bot-v1', 'name': 'BOT_REL release by github-actions[bot]', 'body': 'seeded', 'target_commitish': main_sha})
rec('BOT_REL', st, j, ['id', 'node_id'])
json.dump(out, open('seed-bot.json', 'w'), indent=1)
