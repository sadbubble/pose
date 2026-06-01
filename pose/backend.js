/* POSE data layer: Supabase (free cloud) or self-hosted FastAPI */
(function () {
  var useSupabase =
    typeof POSE_SUPABASE_URL === 'string' &&
    POSE_SUPABASE_URL &&
    typeof POSE_SUPABASE_ANON_KEY === 'string' &&
    POSE_SUPABASE_ANON_KEY;

  var supabase = null;
  if (useSupabase && window.supabase) {
    supabase = window.supabase.createClient(POSE_SUPABASE_URL, POSE_SUPABASE_ANON_KEY);
  }

  var API_BASE = (function () {
    if (useSupabase) return '';
    if (typeof POSE_API_BASE !== 'undefined' && POSE_API_BASE) return POSE_API_BASE.replace(/\/$/, '');
    if (location.protocol === 'file:') return 'http://127.0.0.1:8080';
    if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
      return location.port === '8080' ? '' : 'http://127.0.0.1:8080';
    }
    return '';
  })();

  function genId() {
    if (window.crypto && crypto.getRandomValues) {
      var a = new Uint8Array(4);
      crypto.getRandomValues(a);
      return Array.from(a, function (b) {
        return b.toString(16).padStart(2, '0');
      }).join('');
    }
    return Math.random().toString(16).slice(2, 10);
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function parseJson(val, fallback) {
    if (val == null || val === '') return fallback;
    if (typeof val === 'object') return val;
    try {
      return JSON.parse(val);
    } catch (e) {
      return fallback;
    }
  }

  function mapEventRow(ev, rsvps, comments, updates) {
    ev.questions = parseJson(ev.questions, []);
    ev.rsvps = (rsvps || []).map(function (r) {
      r.answers = parseJson(r.answers, {});
      return r;
    });
    ev.comments = (comments || []).map(function (c) {
      c.reactions = parseJson(c.reactions, {});
      return c;
    });
    ev.updates = updates || [];
    return ev;
  }

  function supabaseGetEvent(id) {
    return supabase
      .from('events')
      .select('*')
      .eq('id', id)
      .single()
      .then(function (res) {
        if (res.error) throw res.error;
        return Promise.all([
          supabase.from('rsvps').select('*').eq('event_id', id).order('created_at'),
          supabase.from('comments').select('*').eq('event_id', id).order('created_at', { ascending: false }),
          supabase.from('updates').select('*').eq('event_id', id).order('created_at', { ascending: false }),
        ]).then(function (parts) {
          return mapEventRow(res.data, parts[0].data, parts[1].data, parts[2].data);
        });
      });
  }

  function supabaseApi(method, path, body) {
    var m = method.toUpperCase();

    if (m === 'POST' && path === '/api/events') {
      var eid = genId();
      return supabase
        .from('events')
        .insert({
          id: eid,
          type: body.type || 'party',
          name: body.name,
          date: body.date || null,
          time: body.time || null,
          location: body.location || null,
          description: body.description || null,
          host: body.host || null,
          style: body.style || 'gradient',
          poster: body.poster || '',
          font: body.font || 'grotesk',
          kaspi: body.kaspi || '',
          questions: JSON.stringify(body.questions || []),
          created_at: nowIso(),
        })
        .then(function (res) {
          if (res.error) throw res.error;
          return { id: eid };
        });
    }

    var eventMatch = path.match(/^\/api\/events\/([^/]+)$/);
    if (m === 'GET' && eventMatch) return supabaseGetEvent(eventMatch[1]);

    var rsvpPost = path.match(/^\/api\/events\/([^/]+)\/rsvps$/);
    if (m === 'POST' && rsvpPost) {
      var rid = genId();
      return supabase
        .from('rsvps')
        .insert({
          id: rid,
          event_id: rsvpPost[1],
          name: body.name,
          status: body.status,
          answers: JSON.stringify(body.answers || {}),
          created_at: nowIso(),
        })
        .then(function (res) {
          if (res.error) throw res.error;
          return { id: rid };
        });
    }

    var rsvpDel = path.match(/^\/api\/rsvps\/([^/]+)$/);
    if (m === 'DELETE' && rsvpDel) {
      return supabase
        .from('rsvps')
        .delete()
        .eq('id', rsvpDel[1])
        .then(function (res) {
          if (res.error) throw res.error;
          return { ok: true };
        });
    }

    var commentPost = path.match(/^\/api\/events\/([^/]+)\/comments$/);
    if (m === 'POST' && commentPost) {
      var cid = genId();
      return supabase
        .from('comments')
        .insert({
          id: cid,
          event_id: commentPost[1],
          name: body.name,
          text: body.text,
          reactions: '{}',
          created_at: nowIso(),
        })
        .then(function (res) {
          if (res.error) throw res.error;
          return { id: cid };
        });
    }

    var reactionPost = path.match(/^\/api\/comments\/([^/]+)\/reactions$/);
    if (m === 'POST' && reactionPost) {
      return supabase
        .from('comments')
        .select('reactions')
        .eq('id', reactionPost[1])
        .single()
        .then(function (res) {
          if (res.error) throw res.error;
          var reactions = parseJson(res.data.reactions, {});
          var cur = reactions[body.emoji] || 0;
          if (cur > 0) {
            reactions[body.emoji] = cur - 1;
            if (reactions[body.emoji] === 0) delete reactions[body.emoji];
          } else {
            reactions[body.emoji] = 1;
          }
          return supabase
            .from('comments')
            .update({ reactions: JSON.stringify(reactions) })
            .eq('id', reactionPost[1])
            .then(function (up) {
              if (up.error) throw up.error;
              return { reactions: reactions };
            });
        });
    }

    var updatePost = path.match(/^\/api\/events\/([^/]+)\/updates$/);
    if (m === 'POST' && updatePost) {
      var uid = genId();
      return supabase
        .from('updates')
        .insert({
          id: uid,
          event_id: updatePost[1],
          text: body.text,
          created_at: nowIso(),
        })
        .then(function (res) {
          if (res.error) throw res.error;
          return { id: uid };
        });
    }

    return Promise.reject(new Error('Unknown API path: ' + path));
  }

  function restApi(method, path, body) {
    var opts = { method: method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    return fetch(API_BASE + path, opts).then(function (r) {
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    });
  }

  window.api = function (method, path, body) {
    if (useSupabase && supabase) return supabaseApi(method, path, body);
    return restApi(method, path, body);
  };

  window.getEvent = function (id, retries) {
    retries = retries || 0;
    return window
      .api('GET', '/api/events/' + id)
      .then(function (ev) {
        window.eventCache[id] = ev;
        return ev;
      })
      .catch(function () {
        if (retries < 2) {
          return new Promise(function (ok) {
            setTimeout(function () {
              ok(window.getEvent(id, retries + 1));
            }, 1500);
          });
        }
        return null;
      });
  };

  window.getCachedEvent = function (id) {
    return window.eventCache[id] || null;
  };

  window.eventCache = {};
  window.POSE_BACKEND = useSupabase ? 'supabase' : 'api';
})();
