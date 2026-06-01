import json, os, base64, urllib.request, ssl, time
from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__, static_folder='.')

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_REPO  = os.environ.get('GITHUB_REPO', 'yardley0527-ux/wp-article-tracker')
FILE_PATH    = 'articles.json'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

_cache = {'data': None, 'sha': None, 'ts': 0}

def gh_get():
    if time.time() - _cache['ts'] < 30 and _cache['data']:
        return _cache['data'], _cache['sha']
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    })
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    r = json.loads(resp.read())
    data = json.loads(base64.b64decode(r['content']).decode())
    _cache.update({'data': data, 'sha': r['sha'], 'ts': time.time()})
    return data, r['sha']

def gh_put(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    data['meta']['last_sync'] = datetime.utcnow().isoformat()
    content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = json.dumps({'message': '更新文章狀態', 'content': content, 'sha': sha}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }, method='PUT')
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    r = json.loads(resp.read())
    new_sha = r['content']['sha']
    _cache.update({'data': data, 'sha': new_sha, 'ts': time.time()})
    return new_sha

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/articles', methods=['GET'])
def get_articles():
    data, _ = gh_get()
    return jsonify(data)

@app.route('/api/articles/<int:article_id>', methods=['PATCH'])
def update_article(article_id):
    data, sha = gh_get()
    body = request.get_json()
    for a in data['articles']:
        if a['id'] == article_id:
            if 'status' in body: a['status'] = body['status']
            if 'note'   in body: a['note']   = body['note']
            break
    else:
        return jsonify({'error': 'not found'}), 404
    data['meta']['done']      = sum(1 for a in data['articles'] if a['status'] == 'done')
    data['meta']['reviewing'] = sum(1 for a in data['articles'] if a['status'] == 'reviewing')
    data['meta']['pending']   = sum(1 for a in data['articles'] if a['status'] == 'pending')
    gh_put(data, sha)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
