// server.js - simple proxy to Elasticsearch with optional PII masking & optional basic auth
const express = require('express');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const ES_BASE = (process.env.ES_BASE || 'http://127.0.0.1:9200').replace(/\/$/, '');
const ES_AUTH = process.env.ES_AUTH || null; // format 'user:pass' if required
const MASK_PII = (process.env.MASK_PII || 'true') === 'true'; // default true
const REQUIRE_PROXY_AUTH = !!(process.env.PROXY_USER && process.env.PROXY_PASS);
const PROXY_USER = process.env.PROXY_USER || '';
const PROXY_PASS = process.env.PROXY_PASS || '';


app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// optional basic auth for proxy endpoint
function checkProxyAuth(req) {
  if (!REQUIRE_PROXY_AUTH) return true;
  const header = req.headers['authorization'];
  if (!header || !header.startsWith('Basic ')) return false;
  const decoded = Buffer.from(header.slice(6), 'base64').toString();
  const [u, p] = decoded.split(':');
  return u === PROXY_USER && p === PROXY_PASS;
}

function maskEmail(email) {
  if (!email) return '';
  const at = email.indexOf('@');
  if (at > 1) return email[0] + '***' + email.substring(at);
  return '***';
}

// 공통 처리 함수: bodyOverride가 있으면 그것을 사용, 없으면 req.body 사용
async function handleBlockedRequest(req, res, bodyOverride) {
  try {
    if (!checkProxyAuth(req)) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const body = bodyOverride || req.body || {};

    const indexPath = body.index || 'blocked-events-*/_search';
    const query = body.query || {
      size: 200,
      sort: [{ "@timestamp": "desc" }],
      query: { match: { "policy.decision": "deny" } },
      _source: [
        "@timestamp",
        "user_metadata.user_id",
        "user_metadata.user_email",
        "user_metadata.student_id",
        "policy.policy_id",
        "policy.reason",
        "http.status"
      ]
    };

    const url = `${ES_BASE}/${indexPath}`;
    const axiosConfig = { headers: { 'Content-Type': 'application/json' } };
    if (ES_AUTH) {
      const parts = ES_AUTH.split(':');
      axiosConfig.auth = { username: parts[0], password: parts[1] || '' };
    }

    const esRes = await axios.post(url, query, axiosConfig);

    // shallow clone and mask PII if requested
    const cloned = JSON.parse(JSON.stringify(esRes.data));
    if (cloned && cloned.hits && cloned.hits.hits) {
      cloned.hits.hits.forEach(h => {
        const s = h._source || {};
        if (s.user_metadata) {
          if (s.user_metadata.user_email && MASK_PII) {
            s.user_metadata.user_email = maskEmail(s.user_metadata.user_email);
          }
          if (s.user_metadata.student_id && MASK_PII) {
            delete s.user_metadata.student_id;
          }
        }
      });
    }

    res.json(cloned);
  } catch (err) {
    console.error('Error fetching from ES:', err && err.response ? err.response.data : err.message);
    const errBody = err && err.response ? err.response.data : String(err);
    const status = (err && err.response && err.response.status) ? err.response.status : 500;
    res.status(status).json({ error: errBody });
  }
}

// POST route uses the common handler (existing behavior)
app.post('/api/blocked', async (req, res) => {
  return handleBlockedRequest(req, res);
});

// GET route: 쿼리 파라미터로 간단하게 호출할 수 있도록 매핑
// 사용법 예:
//  - 기본: GET /api/blocked
//  - 인덱스 지정: GET /api/blocked?index=blocked-events-*/_search
//  - 간단 size 오버라이드: GET /api/blocked?size=5
//  - 전체 ES query JSON 전달: GET /api/blocked?query=<urlencoded JSON>
//    예: ?query=%7B%22size%22%3A5%7D  ({"size":5} 의 URL 인코딩)
app.get('/api/blocked', async (req, res) => {
  try {
    // build a body override from query params
    const bodyOverride = {};

    if (req.query.index) {
      bodyOverride.index = req.query.index;
    }

    if (req.query.query) {
      // query 파라가 JSON 문자열로 들어오면 파싱
      try {
        bodyOverride.query = JSON.parse(req.query.query);
      } catch (e) {
        return res.status(400).json({ error: 'Invalid JSON in query parameter "query"' });
      }
    } else {
      // query 파라가 없으면 size 파라로 간단 오버라이드 가능
      if (req.query.size) {
        const size = parseInt(req.query.size, 10);
        if (!isNaN(size)) {
          bodyOverride.query = {
            size: size,
            sort: [{ "@timestamp": "desc" }],
            query: { match: { "policy.decision": "deny" } },
            _source: [
              "@timestamp",
              "user_metadata.user_id",
              "user_metadata.user_email",
              "user_metadata.student_id",
              "policy.policy_id",
              "policy.reason",
              "http.status"
            ]
          };
        }
      }
    }

    return handleBlockedRequest(req, res, Object.keys(bodyOverride).length ? bodyOverride : undefined);
  } catch (err) {
    console.error('Error in GET /api/blocked:', err);
    res.status(500).json({ error: String(err) });
  }
});

// optional simple health endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', target_es: ES_BASE, mask_pii: MASK_PII });
});

app.listen(PORT, () => {
  console.log(`Proxy listening on http://localhost:${PORT} -> ES ${ES_BASE}`);
  if (REQUIRE_PROXY_AUTH) console.log('Proxy requires basic auth for /api/blocked');
});
// robust summary endpoint - paste/replace into your server.js
app.get('/api/blocked/summary', async (req, res) => {
  try {
    if (!checkProxyAuth(req)) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const indexPath = req.query.index || 'blocked-events-*/_search';

    const aggBody = {
      size: 0,
      track_total_hits: true,
      aggs: {
        by_policy_keyword: { terms: { field: 'policy.policy_id.keyword', size: 50 } },
        by_policy_raw:     { terms: { field: 'policy.policy_id',         size: 50 } },
        by_reason_keyword: { terms: { field: 'policy.reason.keyword',    size: 50 } },
        by_reason_raw:     { terms: { field: 'policy.reason',            size: 50 } }
      }
    };

    const url = `${ES_BASE}/${indexPath}`;
    const axiosConfig = { headers: { 'Content-Type': 'application/json' } };
    if (ES_AUTH) {
      const parts = ES_AUTH.split(':');
      axiosConfig.auth = { username: parts[0], password: parts[1] || '' };
    }

    const esRes = await axios.post(url, aggBody, axiosConfig);
    const aggs = esRes.data.aggregations || {};
    const total = (esRes.data.hits && esRes.data.hits.total)
      ? (typeof esRes.data.hits.total === 'object' ? esRes.data.hits.total.value : esRes.data.hits.total)
      : 0;

    function mergeBuckets(keywordBuckets, rawBuckets) {
      const map = new Map();
      (keywordBuckets || []).forEach(b => map.set(b.key, (map.get(b.key) || 0) + b.doc_count));
      (rawBuckets || []).forEach(b => map.set(b.key, (map.get(b.key) || 0) + b.doc_count));
      return Array.from(map.entries()).map(([key, count]) => ({ key, count })).sort((a,b) => b.count - a.count);
    }

    const policyBuckets = mergeBuckets(
      (aggs.by_policy_keyword && aggs.by_policy_keyword.buckets),
      (aggs.by_policy_raw && aggs.by_policy_raw.buckets)
    );

    const reasonBuckets = mergeBuckets(
      (aggs.by_reason_keyword && aggs.by_reason_keyword.buckets),
      (aggs.by_reason_raw && aggs.by_reason_raw.buckets)
    );

    const policyMap = {
      'OWNERSHIP_CHECK': 'Ownership mismatch (IDOR)',
      'RATE_LIMIT': 'Rate limiting exceeded',
      'AUTHZ_ADMIN_ONLY': 'Admin-only endpoint blocked'
    };

    const policies = policyBuckets.map(b => ({ policy_id: b.key, count: b.count, name: policyMap[b.key] || null }));
    const reasons  = reasonBuckets.map(b => ({ reason: b.key, count: b.count }));

    const result = { index: indexPath, total_hits: total, summary: { policies, reasons } };

    // fallback: if no hits and no agg results, return small sample documents for debugging
    if (total === 0 && policies.length === 0 && reasons.length === 0) {
      const sampleBody = {
        size: 5,
        sort: [{ "@timestamp": "desc" }],
        _source: ["@timestamp","policy.policy_id","policy.reason","user_metadata.user_email","user_metadata.user_id"]
      };
      const sampleRes = await axios.post(url, sampleBody, axiosConfig);
      result.samples = (sampleRes.data.hits && sampleRes.data.hits.hits) ? sampleRes.data.hits.hits.map(h => h._source) : [];
    }

    return res.json(result);
  } catch (err) {
    console.error('Error fetching summary from ES:', err && err.response ? err.response.data : err.message);
    const errBody = err && err.response ? err.response.data : String(err);
    const status = (err && err.response && err.response.status) ? err.response.status : 500;
    res.status(status).json({ error: errBody });
  }
});
// Replace your existing /api/blocked/summary handler with this robust handler
app.get('/api/blocked/summary', async (req, res) => {
  try {
    if (!checkProxyAuth(req)) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const indexPath = req.query.index || 'blocked-events-*/_search';
    const nowWindow = req.query.window || 'now-24h'; // allow override via ?window=
    const sizeLimit = 50; // how many top terms to return

    const aggBody = {
      size: 0,
      track_total_hits: true,
      query: {
        range: {
          "@timestamp": { "gte": nowWindow, "lte": "now" }
        }
      },
      aggs: {
        by_policy_keyword: { terms: { field: 'policy.policy_id.keyword', size: sizeLimit } },
        by_policy_raw:     { terms: { field: 'policy.policy_id',         size: sizeLimit } },
        by_reason_keyword: { terms: { field: 'policy.reason.keyword',    size: sizeLimit } },
        by_reason_raw:     { terms: { field: 'policy.reason',            size: sizeLimit } },
        by_time: {
          date_histogram: {
            field: '@timestamp',
            fixed_interval: '1h',
            min_doc_count: 0,
            extended_bounds: { min: nowWindow, max: 'now' }
          }
        }
      }
    };

    const url = `${ES_BASE}/${indexPath}`;
    const axiosConfig = { headers: { 'Content-Type': 'application/json' } };
    if (ES_AUTH) {
      const parts = ES_AUTH.split(':');
      axiosConfig.auth = { username: parts[0], password: parts[1] || '' };
    }

    const esRes = await axios.post(url, aggBody, axiosConfig);
    const aggs = esRes.data.aggregations || {};
    const total = (esRes.data.hits && esRes.data.hits.total)
      ? (typeof esRes.data.hits.total === 'object' ? esRes.data.hits.total.value : esRes.data.hits.total)
      : 0;

    function mergeBuckets(keywordBuckets, rawBuckets) {
      const map = new Map();
      (keywordBuckets || []).forEach(b => map.set(String(b.key), (map.get(String(b.key)) || 0) + b.doc_count));
      (rawBuckets || []).forEach(b => map.set(String(b.key), (map.get(String(b.key)) || 0) + b.doc_count));
      return Array.from(map.entries())
        .map(([key, count]) => ({ key, count }))
        .sort((a, b) => b.count - a.count);
    }

    const policyBuckets = mergeBuckets(
      (aggs.by_policy_keyword && aggs.by_policy_keyword.buckets),
      (aggs.by_policy_raw && aggs.by_policy_raw.buckets)
    );

    const reasonBuckets = mergeBuckets(
      (aggs.by_reason_keyword && aggs.by_reason_keyword.buckets),
      (aggs.by_reason_raw && aggs.by_reason_raw.buckets)
    );

    const policyMap = {
      'OWNERSHIP_CHECK': 'Ownership mismatch (IDOR)',
      'RATE_LIMIT': 'Rate limiting exceeded',
      'AUTHZ_ADMIN_ONLY': 'Admin-only endpoint blocked'
    };

    const policies = policyBuckets.map(b => ({ policy_id: b.key, count: b.count, name: policyMap[b.key] || null }));
    const reasons  = reasonBuckets.map(b => ({ reason: b.key, count: b.count }));

    const timeBuckets = (aggs.by_time && aggs.by_time.buckets) ? aggs.by_time.buckets : [];
    const time_series = timeBuckets.map(b => ({
      ts: b.key_as_string,         // ISO timestamp string for the bucket start
      count: b.doc_count
    }));

    const result = {
      index: indexPath,
      total_hits: total,
      summary: { policies, reasons },
      time_series
    };

    // fallback samples for debugging: include recent documents when there are hits but no aggs (or if caller requested samples)
    const needSamples = req.query.samples === '1' || (total > 0 && (policies.length === 0 && reasons.length === 0));
    if (needSamples) {
      const sampleBody = {
        size: 5,
        sort: [{ "@timestamp": "desc" }],
        _source: ["@timestamp","policy.policy_id","policy.reason","user_metadata.user_email","user_metadata.user_id"]
      };
      const sampleRes = await axios.post(url, sampleBody, axiosConfig);
      result.samples = (sampleRes.data.hits && sampleRes.data.hits.hits) ? sampleRes.data.hits.hits.map(h => h._source) : [];
    }

    return res.json(result);
  } catch (err) {
    console.error('Error fetching summary from ES:', err && err.response ? err.response.data : err.message);
    const errBody = err && err.response ? err.response.data : String(err);
    const status = (err && err.response && err.response.status) ? err.response.status : 500;
    res.status(status).json({ error: errBody });
  }
});
app.get('/api/blocked/events', (req, res) => {
  try {
    const eventsPath = path.join(__dirname, '..', 'public', 'data', 'block_events.json');
    const fileContent = fs.readFileSync(eventsPath, 'utf8');
    const events = JSON.parse(fileContent);  // 표준 JSON 배열 파싱
    
    res.json({ 
      total: events.length, 
      events: events 
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
app.get('/api/file-stat', (req, res) => {
  try {
    const eventsPath = path.join(__dirname, '..', 'public', 'data', 'block_events.json');  // ← '..' 추가!
    
    if (fs.existsSync(eventsPath)) {
      const stat = fs.statSync(eventsPath);
      res.json({ mtime: stat.mtime.getTime(), exists: true });
    } else {
      res.json({ mtime: null, exists: false });
    }
  } catch (err) {
    res.status(500).json({ error: 'server_error' });
  }
});
app.get('/api/blocked/list', (req, res) => {
  try {
    const eventsPath = path.join(__dirname, '..', 'public', 'data', 'block_events.json');
    const fileContent = fs.readFileSync(eventsPath, 'utf8');
    const events = fileContent
      .trim()
      .split('\n')
      .map(line => {
        try {
          return JSON.parse(line);
        } catch (e) {
          return null;
        }
      })
      .filter(e => e !== null);
    
    res.json({ total: events.length, events: events });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
app.get('/api/blocked/raw', (req, res) => {
  try {
    const eventsPath = path.join(__dirname, '..', 'public', 'data', 'block_events.json');
    const fileContent = fs.readFileSync(eventsPath, 'utf8');
    const events = fileContent
      .trim()
      .split('\n')
      .map(line => {
        try {
          return JSON.parse(line);
        } catch (e) {
          return null;
        }
      })
      .filter(e => e !== null);
    
    res.json({ total: events.length, events: events });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
app.get('/api/debug', (req, res) => {
  try {
    const eventsPath = path.join(__dirname, '..', 'public', 'data', 'block_events.json');
    const fileContent = fs.readFileSync(eventsPath, 'utf8');
    const parsed = JSON.parse(fileContent);
    
    res.json({
      path: eventsPath,
      fileExists: fs.existsSync(eventsPath),
      fileSize: fileContent.length,
      parsedType: typeof parsed,
      parsedIsArray: Array.isArray(parsed),
      parsedLength: Array.isArray(parsed) ? parsed.length : 'not-array',
      firstItem: Array.isArray(parsed) ? parsed[0] : null,
      rawFileStart: fileContent.substring(0, 100),
      rawFileEnd: fileContent.substring(fileContent.length - 100)
    });
  } catch (err) {
    res.status(500).json({ 
      error: err.message,
      stack: err.stack
    });
  }
});
