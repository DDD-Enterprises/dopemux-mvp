import type {
  EngineInterface,
  Register,
  RenderElement,
  SessionCompactTrigger,
  Timer,
  ToolCallInput,
  ToolCallResult,
  TurnCompleteInput,
} from 'claude-code'

// dopemux-memory-bridge: a local, no-network memory outbox.
//
// It records a derived digest of each turn (goal, relative file paths,
// marker-detected decisions, completed todo titles) into a per-session JSONL
// ring under `<repo-root>/.dopemux/memory-bridge/`, shows how many rows wait
// in the status line, and draws a one-line welcome-back band after a break.
//
// There is no `$.http.fetch`, no `dopemux` call and no ConPort or dope-memory
// access anywhere in this file. The one subprocess is `git status --porcelain`
// (band only). Every hook body is wrapped so an exception never reaches the
// person, and the observing hooks hand `next(e)` back untouched.
//
// The engine's static reader follows `$` only through functions declared at
// the top of this file, so the helpers below take `$` and the session's state
// object as arguments instead of closing over them.

const MINUTE = 60_000
const DEFAULT_IDLE_MINUTES = 30
const MIN_IDLE_MINUTES = 5
const MAX_IDLE_MINUTES = 1440

const FILE_CAP_BYTES = 1_048_576 // one outbox generation file: 1 MiB
const STORE_CAP_BYTES = 262_144 // the in-memory fallback kept in $.store
const ROW_CAP_BYTES = 8_192
const CAP_MARGIN_BYTES = 512 // room for the header and footer lines

const GOAL_CHARS = 160
const DECISION_CHARS = 200
const TITLE_CHARS = 120
const PATH_CHARS = 240
const NOTE_CHARS = 2_000
const MAX_DECISIONS = 3
const MAX_FILES = 30
const MAX_TODOS = 10

const WRITE_TIMEOUT_MS = 3_000
const INIT_TIMEOUT_MS = 1_500
const END_FLUSH_MS = 800
const GIT_TIMEOUT_MS = 3_000
const MAX_SESSIONS_READ = 8
const MAX_ROOT_WALK = 40
const STORE_KEEP_SESSIONS = 3

type Kind = 'turn' | 'compact' | 'end' | 'task' | 'note'
type RowState = 'pending' | 'sent' | 'dead'
type IntendedEvent = 'task.completed' | 'manual.memory_store' | null

const KINDS: readonly string[] = ['turn', 'compact', 'end', 'task', 'note']
const STATES: readonly string[] = ['pending', 'sent', 'dead']

type OutboxRow = {
  v: 1
  id: string
  ts: string
  kind: Kind
  session_id: string
  cwd_rel: string
  goal: string
  files_touched: string[]
  decisions: string[]
  todos_completed: string[]
  note?: string
  intended_event: IntendedEvent
  state: RowState
  attempts: number
}

type Entry = { row: OutboxRow; line: string; bytes: number }

type Generation = { gen: number; dropped: number; rows: OutboxRow[] }

type Ring = {
  sid: string
  entries: Entry[]
  ids: Set<string>
  bytes: number
  gen: number
  dropped: number
  mode: 'unknown' | 'file' | 'memory'
  loaded: boolean
  loading: Promise<void> | undefined
  dirty: boolean
  flushing: boolean
  flushPromise: Promise<void> | undefined
  failed: boolean
}

type PriorSessions = { rows: OutboxRow[]; pending: number }

// One module load's state. Module-local on purpose: a reload starts fresh, and
// everything that matters is already in the outbox file.
type Bridge = {
  idleMs: number
  cwd: string | undefined
  root: string | undefined
  rootFor: string | undefined
  rings: Map<string, Ring>
  foldedPending: number // pending rows of closed (cleared) sessions and older files
  foldedDropped: number
  turnId: string
  goal: string
  files: string[]
  todosDone: string[]
  prevCompleted: Map<string, number>
  compactSeq: number
  lastActivityAt: number | undefined
  idleTimer: Timer | undefined
  bandLine: string | undefined
  bandBusy: boolean
  gitInFlight: boolean
  isEnded: boolean
}

type AppendInput = {
  kind: Kind
  turnId: string
  disc?: string
  sid?: string
  goal?: string
  files?: readonly string[]
  decisions?: readonly string[]
  todos?: readonly string[]
  note?: string
  intended?: IntendedEvent
}

// --- redaction and text ----------------------------------------------------------

// Deterministic, in-module. Masks the shapes the repo's own redactor misses
// (sk-ant keys, URL userinfo, emails, DATABASE_URL= and friends) as well as the
// ones it has. Runs on every string before it is capped and written.
const REDACTIONS: readonly (readonly [RegExp, string])[] = [
  [/-----BEGIN [A-Z0-9 ]+-----[\s\S]*?(?:-----END [A-Z0-9 ]+-----|$)/g, '[REDACTED:pem]'],
  [/\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}/g, '[REDACTED:jwt]'],
  [/\bsk-ant-[A-Za-z0-9_-]{6,}/g, '[REDACTED:key]'],
  [/\bsk-[A-Za-z0-9_-]{16,}/g, '[REDACTED:key]'],
  [/\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}/g, '[REDACTED:key]'],
  [/\bgithub_pat_[A-Za-z0-9_]{20,}/g, '[REDACTED:key]'],
  [/\bxox[abprs]-[A-Za-z0-9-]{10,}/g, '[REDACTED:key]'],
  [/\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g, '[REDACTED:key]'],
  [/\bBearer\s+[A-Za-z0-9._~+/=-]{8,}/gi, 'Bearer [REDACTED]'],
  [/(\b[a-z][a-z0-9+.-]*:\/\/)[^\s/@]+@/gi, '$1[REDACTED]@'],
  [/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b/g, '[REDACTED:email]'],
  [
    /\b([A-Za-z0-9_.-]*(?:DATABASE_URL|PASSWORD|PASSWD|PWD|SECRET|TOKEN|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|CREDENTIALS?)[A-Za-z0-9_.-]*|[A-Z][A-Z0-9_]*_(?:URL|KEY))\s*=\s*("[^"]*"|'[^']*'|[^\s,;]+)/gi,
    '$1=[REDACTED]',
  ],
  [/"([A-Za-z0-9_.-]*(?:password|passwd|secret|token|api_?key|private_?key)[A-Za-z0-9_.-]*)"\s*:\s*"[^"]*"/gi, '"$1":"[REDACTED]"'],
  [/\/(?:Users|home)\/[^/\s]+\//g, '~/'],
]

function redact(text: string): string {
  let out = text
  for (const [pattern, replacement] of REDACTIONS) out = out.replace(pattern, replacement)
  return out
}

function cap(text: string, chars: number): string {
  return text.length <= chars ? text : Array.from(text).slice(0, chars).join('')
}

// Redact first (so a secret cut by the cap is never left half-masked), then
// collapse whitespace and cap. A huge input is trimmed before the regexes run.
function clean(text: unknown, chars: number): string {
  if (typeof text !== 'string') return ''
  const bounded = text.length > chars * 4 + 200 ? text.slice(0, chars * 4 + 200) : text
  return cap(redact(bounded).replace(/\s+/g, ' ').trim(), chars)
}

const DECISION_LINE =
  /^[ \t]*(?:(?:\*\*|__)?(?:Decision|DECISION):(?:\*\*|__)?|(?:\*\*|__)(?:Decision|DECISION)(?:\*\*|__):)[ \t]*(\S.*)$/gm

// Marker-only: a line that starts `Decision:` or `DECISION:` (optionally bold).
function decisionsOf(answer: unknown): string[] {
  if (typeof answer !== 'string') return []
  const found: string[] = []
  for (const match of answer.matchAll(DECISION_LINE)) {
    const text = clean(match[1], DECISION_CHARS)
    if (text !== '') found.push(text)
    if (found.length >= MAX_DECISIONS) break
  }
  return found
}

function byteLength(text: string): number {
  return new TextEncoder().encode(text).length
}

async function digest24(input: string): Promise<string> {
  const buffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(input))
  let hex = ''
  for (const byte of new Uint8Array(buffer)) hex += byte.toString(16).padStart(2, '0')
  return hex.slice(0, 24)
}

// --- paths -----------------------------------------------------------------------

function normalizePath(path: string): string {
  const parts: string[] = []
  for (const part of path.split('/')) {
    if (part === '' || part === '.') continue
    if (part === '..') parts.pop()
    else parts.push(part)
  }
  return (path.startsWith('/') ? '/' : '') + parts.join('/')
}

function joinPath(dir: string, name: string): string {
  return dir === '/' ? `/${name}` : `${dir}/${name}`
}

function relativeTo(root: string, file: string): string | undefined {
  const base = normalizePath(root)
  const target = normalizePath(file)
  if (target === base) return '.'
  const prefix = base === '/' ? '/' : `${base}/`
  return target.startsWith(prefix) ? target.slice(prefix.length) : undefined
}

function safeId(sessionId: string): string {
  const clean = sessionId.replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 80)
  return clean === '' ? 'unknown' : clean
}

function outboxDir(root: string): string {
  return `${normalizePath(root)}/.dopemux/memory-bridge`
}

// Generation 1 lives in the primary file, 2 in the alternate, 3 in the primary...
function generationPath(root: string, key: string, gen: number): string {
  const base = `${outboxDir(root)}/outbox-${key}`
  return (gen - 1) % 2 === 0 ? `${base}.jsonl` : `${base}.alt.jsonl`
}

// The same upward `.git`/`.dopemux` walk as src/dopemux/memory/capture_client.py
// `_repo_root_from_start`: the nearest ancestor holding either marker.
async function findRoot($: EngineInterface, cwd: string): Promise<string | undefined> {
  let dir = normalizePath(cwd)
  for (let step = 0; step < MAX_ROOT_WALK; step += 1) {
    if ((await $.fs.exists(joinPath(dir, '.git'))) || (await $.fs.exists(joinPath(dir, '.dopemux')))) {
      return dir
    }
    if (dir === '/' || dir === '') return undefined
    const cut = dir.lastIndexOf('/')
    dir = cut <= 0 ? '/' : dir.slice(0, cut)
  }
  return undefined
}

async function resolveRoot($: EngineInterface, s: Bridge): Promise<void> {
  try {
    const cwd = s.cwd ?? (await $.session.cwd())
    if (s.rootFor === cwd) return
    s.cwd = cwd
    s.root = await findRoot($, cwd)
    s.rootFor = cwd
  } catch {
    // Leave the previous answer; the outbox then stays in memory.
  }
}

// --- the outbox file format --------------------------------------------------------

function isRow(value: unknown): value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false
  const r = value as Record<string, unknown>
  return (
    r.v === 1 &&
    typeof r.id === 'string' &&
    typeof r.ts === 'string' &&
    typeof r.session_id === 'string' &&
    typeof r.kind === 'string' &&
    KINDS.includes(r.kind) &&
    typeof r.state === 'string' &&
    STATES.includes(r.state)
  )
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((x): x is string => typeof x === 'string') : []
}

function toRow(r: Record<string, unknown>): OutboxRow {
  const row: OutboxRow = {
    v: 1,
    id: r.id as string,
    ts: r.ts as string,
    kind: r.kind as Kind,
    session_id: r.session_id as string,
    cwd_rel: typeof r.cwd_rel === 'string' ? r.cwd_rel : '.',
    goal: typeof r.goal === 'string' ? r.goal : '',
    files_touched: strings(r.files_touched),
    decisions: strings(r.decisions),
    todos_completed: strings(r.todos_completed),
    intended_event:
      r.intended_event === 'task.completed' || r.intended_event === 'manual.memory_store'
        ? r.intended_event
        : null,
    state: r.state as RowState,
    attempts: typeof r.attempts === 'number' ? r.attempts : 0,
  }
  if (typeof r.note === 'string') row.note = r.note
  return row
}

// A generation is valid only when it opens with its header and closes with a
// footer of the same number whose row count matches the lines between them. A
// torn write lacks the footer, so it is never mistaken for a complete file.
function parseGeneration(text: string): Generation | undefined {
  const lines = text.split('\n').filter(line => line.trim() !== '')
  if (lines.length < 2) return undefined
  try {
    const head = JSON.parse(lines[0] ?? '') as Record<string, unknown>
    const foot = JSON.parse(lines[lines.length - 1] ?? '') as Record<string, unknown>
    if (head.meta !== 'gen' || foot.meta !== 'eof') return undefined
    if (typeof head.gen !== 'number' || head.gen !== foot.gen) return undefined
    if (foot.rows !== lines.length - 2) return undefined
    const rows: OutboxRow[] = []
    for (const line of lines.slice(1, -1)) {
      try {
        const parsed: unknown = JSON.parse(line)
        if (isRow(parsed)) rows.push(toRow(parsed))
      } catch {
        // Tolerant: one bad line costs that line only.
      }
    }
    return {
      gen: head.gen,
      dropped: typeof head.dropped === 'number' ? head.dropped : 0,
      rows,
    }
  } catch {
    return undefined
  }
}

function newest(a: Generation | undefined, b: Generation | undefined): Generation | undefined {
  if (a === undefined) return b
  if (b === undefined) return a
  return a.gen >= b.gen ? a : b
}

async function readGeneration($: EngineInterface, path: string): Promise<Generation | undefined> {
  try {
    const text = await $.fs.read(path)
    return typeof text === 'string' ? parseGeneration(text) : undefined
  } catch {
    return undefined
  }
}

function serialize(ring: Ring, gen: number): string {
  const head = JSON.stringify({ v: 1, meta: 'gen', gen, session_id: ring.sid, dropped: ring.dropped })
  const foot = JSON.stringify({ v: 1, meta: 'eof', gen, rows: ring.entries.length })
  return [head, ...ring.entries.map(entry => entry.line), foot].join('\n') + '\n'
}

function entryOf(row: OutboxRow): Entry {
  const line = JSON.stringify(row)
  return { row, line, bytes: byteLength(line) + 1 }
}

// Over the cap: drop the oldest 'sent' rows first, then 'dead', then the
// oldest 'pending', and count every drop.
function enforceCap(ring: Ring, capBytes: number): void {
  const budget = capBytes - CAP_MARGIN_BYTES
  if (ring.bytes <= budget) return
  const doomed = new Set<Entry>()
  let bytes = ring.bytes
  for (const state of ['sent', 'dead', 'pending'] as const) {
    for (const entry of ring.entries) {
      if (bytes <= budget) break
      if (entry.row.state === state && !doomed.has(entry)) {
        doomed.add(entry)
        bytes -= entry.bytes
      }
    }
  }
  if (doomed.size === 0) return
  ring.entries = ring.entries.filter(entry => !doomed.has(entry))
  ring.bytes = bytes
  ring.dropped += doomed.size
  ring.dirty = true
}

// A row is at most 8 KB on the wire: shrink the optional parts, in order, until
// it fits.
function fitRow(row: OutboxRow): OutboxRow {
  const fits = (r: OutboxRow) => byteLength(JSON.stringify(r)) <= ROW_CAP_BYTES
  const steps: ((r: OutboxRow) => OutboxRow)[] = [
    r => ({ ...r, files_touched: r.files_touched.slice(0, 10) }),
    r => ({ ...r, todos_completed: r.todos_completed.slice(0, 3) }),
    r => ({ ...r, decisions: r.decisions.slice(0, 1) }),
    r => ({ ...r, files_touched: [] }),
    r => (r.note === undefined ? r : { ...r, note: cap(r.note, 500) }),
    r => ({ ...r, todos_completed: [] }),
    r => ({ ...r, goal: cap(r.goal, 80), decisions: [] }),
  ]
  let current = row
  for (const step of steps) {
    if (fits(current)) return current
    current = step(current)
  }
  return current
}

// --- the ring ----------------------------------------------------------------------

function ringFor(s: Bridge, sid: string): Ring {
  let ring = s.rings.get(sid)
  if (ring === undefined) {
    ring = {
      sid,
      entries: [],
      ids: new Set(),
      bytes: 0,
      gen: 0,
      dropped: 0,
      mode: 'unknown',
      loaded: false,
      loading: undefined,
      dirty: false,
      flushing: false,
      flushPromise: undefined,
      failed: false,
    }
    s.rings.set(sid, ring)
  }
  return ring
}

function adopt(ring: Ring, found: Generation): void {
  ring.entries = found.rows.map(entryOf)
  ring.ids = new Set(found.rows.map(row => row.id))
  ring.bytes = ring.entries.reduce((sum, entry) => sum + entry.bytes, 0)
  ring.gen = found.gen
  ring.dropped = found.dropped
  enforceCap(ring, FILE_CAP_BYTES)
}

// Loads what an earlier run of this same session id left: the newest valid
// generation from the file, or from $.store when there is no outbox directory.
async function ensureLoaded($: EngineInterface, s: Bridge, ring: Ring): Promise<void> {
  if (ring.loaded) return
  if (ring.loading !== undefined) return ring.loading
  ring.loading = (async () => {
    try {
      await resolveRoot($, s)
      const root = s.root
      if (root !== undefined && (await $.fs.exists(`${normalizePath(root)}/.dopemux`))) {
        ring.mode = 'file'
        const key = safeId(ring.sid)
        const first = await readGeneration($, generationPath(root, key, 1))
        const second = await readGeneration($, generationPath(root, key, 2))
        const best = newest(first, second)
        if (best !== undefined) adopt(ring, best)
      } else {
        ring.mode = 'memory'
        const saved: unknown = await $.store.get(`outbox:${safeId(ring.sid)}`)
        if (typeof saved === 'object' && saved !== null) {
          const record = saved as Record<string, unknown>
          const rows = Array.isArray(record.rows) ? record.rows.filter(isRow).map(toRow) : []
          if (rows.length > 0) {
            adopt(ring, {
              gen: typeof record.gen === 'number' ? record.gen : 0,
              dropped: typeof record.dropped === 'number' ? record.dropped : 0,
              rows,
            })
          }
        }
      }
    } catch {
      // A failed load starts the ring empty; the next write rewrites the file.
    } finally {
      ring.loaded = true
      ring.loading = undefined
    }
  })()
  return ring.loading
}

async function pruneStore($: EngineInterface, keep: string): Promise<void> {
  try {
    const keys = (await $.store.keys()).filter(key => key.startsWith('outbox:') && key !== keep)
    for (const key of keys.slice(0, Math.max(0, keys.length - (STORE_KEEP_SESSIONS - 1)))) {
      await $.store.delete(key)
    }
  } catch {
    // Pruning is best effort.
  }
}

// One write of the ring. The snapshot is serialized before the call, so rows
// appended meanwhile go out in the next pass.
async function persistOnce($: EngineInterface, s: Bridge, ring: Ring): Promise<void> {
  await resolveRoot($, s)
  const root = s.root
  if (root !== undefined && (await $.fs.exists(`${normalizePath(root)}/.dopemux`))) {
    ring.mode = 'file'
    const gen = ring.gen + 1
    await $.fs.write(generationPath(root, safeId(ring.sid), gen), serialize(ring, gen))
    ring.gen = gen
    return
  }
  ring.mode = 'memory'
  enforceCap(ring, STORE_CAP_BYTES)
  const key = `outbox:${safeId(ring.sid)}`
  await $.store.set(key, {
    v: 1,
    gen: ring.gen + 1,
    dropped: ring.dropped,
    rows: ring.entries.map(entry => entry.row),
  })
  ring.gen += 1
  await pruneStore($, key)
}

// `$.fs.write` is raced against a timer, but a raced call is not cancelled:
// the ring's `flushing` flag stays set until the real call settles, so a hung
// write can never be joined by a second one.
async function persist($: EngineInterface, s: Bridge, ring: Ring): Promise<boolean> {
  const work = persistOnce($, s, ring).then(
    () => true,
    () => false,
  )
  let timer: Timer | undefined
  try {
    const timeout = new Promise<'timeout'>(resolve => {
      timer = $.clock.after(WRITE_TIMEOUT_MS, () => resolve('timeout'))
    })
    const first = await Promise.race([work, timeout])
    if (first !== 'timeout') return first
    ring.failed = true
    renderStatus($, s)
    return await work
  } finally {
    timer?.cancel()
  }
}

function flush($: EngineInterface, s: Bridge, ring: Ring): Promise<void> {
  if (ring.flushing && ring.flushPromise !== undefined) return ring.flushPromise
  ring.flushing = true
  ring.flushPromise = (async () => {
    try {
      while (ring.dirty) {
        ring.dirty = false
        const isWritten = await persist($, s, ring)
        ring.failed = !isWritten
        if (!isWritten) {
          // Keep the rows; the next append (or the end of the session) retries.
          ring.dirty = true
          break
        }
        renderStatus($, s)
      }
    } catch {
      ring.failed = true
    } finally {
      ring.flushing = false
      renderStatus($, s)
    }
  })()
  return ring.flushPromise
}

async function boundedFlush($: EngineInterface, s: Bridge, ring: Ring): Promise<void> {
  let timer: Timer | undefined
  try {
    const timeout = new Promise<void>(resolve => {
      timer = $.clock.after(END_FLUSH_MS, () => resolve())
    })
    await Promise.race([flush($, s, ring), timeout])
  } finally {
    timer?.cancel()
  }
}

// --- status line -------------------------------------------------------------------

function renderStatus($: EngineInterface, s: Bridge): void {
  if (s.isEnded) return
  try {
    let pending = s.foldedPending
    let dropped = s.foldedDropped
    let isFailed = false
    let isMemory = false
    for (const ring of s.rings.values()) {
      for (const entry of ring.entries) if (entry.row.state === 'pending') pending += 1
      dropped += ring.dropped
      if (ring.failed) isFailed = true
      if (ring.mode === 'memory') isMemory = true
    }
    let text: string
    if (isFailed) text = '⚠ outbox write failed'
    else if (isMemory) text = '📮 memory-only'
    else text = pending === 0 ? '📮 clear' : `📮 ${pending} pending`
    if (dropped > 0) text += ` +${dropped} dropped`
    $.ui.status(text)
  } catch {
    // never surface
  }
}

// --- appending a record --------------------------------------------------------------

async function append($: EngineInterface, s: Bridge, input: AppendInput): Promise<void> {
  const sid = input.sid ?? (await $.session.id())
  const ring = ringFor(s, sid)
  await ensureLoaded($, s, ring)
  await resolveRoot($, s)

  const now = await $.clock.now()
  const id = await digest24(
    `${sid}\u0000${input.turnId}\u0000${input.kind}${input.disc === undefined ? '' : `\u0000${input.disc}`}`,
  )
  if (ring.ids.has(id)) return

  const cwdRel =
    s.root !== undefined && s.cwd !== undefined ? (relativeTo(s.root, s.cwd) ?? '.') : '.'
  const row = fitRow({
    v: 1,
    id,
    ts: new Date(now).toISOString(),
    kind: input.kind,
    session_id: sid,
    cwd_rel: cwdRel,
    goal: input.goal ?? '',
    files_touched: [...(input.files ?? [])].slice(0, MAX_FILES),
    decisions: [...(input.decisions ?? [])].slice(0, MAX_DECISIONS),
    todos_completed: [...(input.todos ?? [])].slice(0, MAX_TODOS),
    ...(input.note === undefined ? {} : { note: clean(input.note, NOTE_CHARS) }),
    intended_event: input.intended ?? null,
    state: 'pending',
    attempts: 0,
  })

  // No await between the id check above and the push: the ring stays consistent.
  ring.ids.add(id)
  const entry = entryOf(row)
  ring.entries.push(entry)
  ring.bytes += entry.bytes
  enforceCap(ring, FILE_CAP_BYTES)
  ring.dirty = true
  renderStatus($, s)
  void flush($, s, ring)
}

// --- capture ---------------------------------------------------------------------------

async function addFile($: EngineInterface, s: Bridge, path: unknown): Promise<void> {
  if (typeof path !== 'string' || path === '') return
  await resolveRoot($, s)
  const base = s.root ?? s.cwd
  if (base === undefined) return
  const absolute = path.startsWith('/') ? path : joinPath(s.cwd ?? base, path)
  const relative = relativeTo(base, absolute)
  if (relative === undefined || relative === '.') return
  const shown = cap(redact(relative), PATH_CHARS)
  if (s.files.length < MAX_FILES && !s.files.includes(shown)) s.files.push(shown)
}

async function observeTodos($: EngineInterface, s: Bridge, todos: unknown): Promise<void> {
  if (!Array.isArray(todos)) return
  const completed = new Map<string, number>()
  for (const todo of todos) {
    if (typeof todo !== 'object' || todo === null) continue
    const item = todo as Record<string, unknown>
    if (item.status !== 'completed') continue
    const title = clean(item.content, TITLE_CHARS)
    if (title === '') continue
    completed.set(title, (completed.get(title) ?? 0) + 1)
  }
  const before = s.prevCompleted
  s.prevCompleted = completed
  for (const [title, count] of completed) {
    for (let seen = before.get(title) ?? 0; seen < count; seen += 1) {
      s.todosDone.push(title)
      await append($, s, {
        kind: 'task',
        turnId: s.turnId,
        disc: `${title}#${seen}`,
        goal: s.goal,
        todos: [title],
        intended: 'task.completed',
      })
    }
  }
}

async function observeTool(
  $: EngineInterface,
  s: Bridge,
  e: ToolCallInput,
  result: ToolCallResult,
): Promise<void> {
  if (s.isEnded) return
  // A call that was refused or errored touched nothing.
  if (result.deny !== undefined || result.isError === true) return
  if (e.tool === 'Edit' || e.tool === 'Write') {
    await addFile($, s, e.file_path)
  } else if (e.tool === 'NotebookEdit') {
    await addFile($, s, e.notebook_path)
  } else if (e.tool === 'TodoWrite' && e.agentId === undefined) {
    await observeTodos($, s, e.todos)
  }
}

function captureTurn($: EngineInterface, s: Bridge, e: TurnCompleteInput): Promise<void> {
  // Snapshot and reset synchronously: the next turn may start before the
  // append below has finished.
  const input: AppendInput = {
    kind: 'turn',
    turnId: e.turnId,
    goal: s.goal,
    files: [...s.files],
    decisions: decisionsOf(e.answer),
    todos: [...s.todosDone],
    intended: null,
  }
  s.files = []
  s.todosDone = []
  const isEmpty =
    input.goal === '' &&
    input.files?.length === 0 &&
    input.decisions?.length === 0 &&
    input.todos?.length === 0
  return isEmpty ? Promise.resolve() : append($, s, input)
}

function captureCompact($: EngineInterface, s: Bridge, trigger: SessionCompactTrigger): Promise<void> {
  s.compactSeq += 1
  return append($, s, {
    kind: 'compact',
    turnId: s.turnId,
    disc: `${trigger}#${s.compactSeq}`,
    goal: s.goal,
    files: [...s.files],
    intended: null,
  })
}

// --- prior sessions and the band ---------------------------------------------------------

// Reads the newest few other sessions' outbox files of this repo (the current
// process's own sessions are in memory and fresher than their files).
async function readPrior($: EngineInterface, s: Bridge): Promise<PriorSessions> {
  const none: PriorSessions = { rows: [], pending: 0 }
  const root = s.root
  if (root === undefined) return none
  try {
    const dir = outboxDir(root)
    const own = new Set([...s.rings.keys()].map(safeId))
    const newestBy = new Map<string, number>()
    for (const entry of await $.fs.list(dir)) {
      const match = /^outbox-(.+?)(?:\.alt)?\.jsonl$/.exec(entry.name)
      if (match === null || entry.kind !== 'file') continue
      const key = match[1] ?? ''
      if (own.has(key)) continue
      newestBy.set(key, Math.max(newestBy.get(key) ?? 0, entry.mtimeMs))
    }
    const keys = [...newestBy.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, MAX_SESSIONS_READ)
      .map(([key]) => key)
    const rows: OutboxRow[] = []
    let pending = 0
    for (const key of keys) {
      const best = newest(
        await readGeneration($, generationPath(root, key, 1)),
        await readGeneration($, generationPath(root, key, 2)),
      )
      if (best === undefined) continue
      rows.push(...best.rows)
      pending += best.rows.filter(row => row.state === 'pending').length
    }
    return { rows, pending }
  } catch {
    return none
  }
}

async function dirtyFileCount($: EngineInterface, s: Bridge): Promise<number | undefined> {
  const cwd = s.root ?? s.cwd
  if (cwd === undefined || s.gitInFlight) return undefined
  s.gitInFlight = true
  let timer: Timer | undefined
  try {
    // The raced call is not cancelled: `gitInFlight` stays set until it settles.
    const run = $.process.run(['git', 'status', '--porcelain'], { cwd, timeoutMs: GIT_TIMEOUT_MS })
    const settled = run.then(
      result => result,
      () => undefined,
    )
    void settled.finally(() => {
      s.gitInFlight = false
    })
    const timeout = new Promise<'timeout'>(resolve => {
      timer = $.clock.after(GIT_TIMEOUT_MS, () => resolve('timeout'))
    })
    const result = await Promise.race([settled, timeout])
    if (result === 'timeout' || result === undefined || result.exitCode !== 0) return undefined
    return result.stdout.split('\n').filter(line => line.trim() !== '').length
  } catch {
    // `$.process` is CLI only; on another surface it may be absent or refuse.
    s.gitInFlight = false
    return undefined
  } finally {
    timer?.cancel()
  }
}

function newestWith(rows: readonly OutboxRow[], has: (row: OutboxRow) => boolean): OutboxRow | undefined {
  let best: OutboxRow | undefined
  for (const row of rows) {
    if (!has(row)) continue
    if (best === undefined || row.ts >= best.ts) best = row
  }
  return best
}

async function refreshBand($: EngineInterface, s: Bridge): Promise<void> {
  if (s.bandBusy) return
  s.bandBusy = true
  try {
    const prior = await readPrior($, s)
    const own = [...s.rings.values()].flatMap(ring => ring.entries.map(entry => entry.row))
    const rows = [...prior.rows, ...own]
    const goalRow = newestWith(rows, row => row.goal !== '')
    if (goalRow === undefined) {
      s.bandLine = undefined
      return
    }
    const decisionRow = newestWith(rows, row => row.decisions.length > 0)
    const decision = decisionRow?.decisions[decisionRow.decisions.length - 1]
    const dirty = await dirtyFileCount($, s)

    let line = `Welcome back - you were on ${goalRow.goal}`
    if (decision !== undefined) line += ` - last decision ${decision}`
    if (dirty !== undefined) line += ` - ${dirty} uncommitted file${dirty === 1 ? '' : 's'}`
    s.bandLine = line
  } catch {
    s.bandLine = undefined
  } finally {
    s.bandBusy = false
  }
}

function redraw($: EngineInterface): void {
  try {
    $.ui.invalidate('ui.render')
  } catch {
    // never surface
  }
}

async function onIdle($: EngineInterface, s: Bridge): Promise<void> {
  if (s.isEnded) return
  await refreshBand($, s)
  redraw($)
}

function armIdle($: EngineInterface, s: Bridge, delayMs: number): void {
  s.idleTimer?.cancel()
  s.idleTimer = undefined
  if (s.isEnded) return
  s.idleTimer = $.clock.after(Math.max(0, delayMs), () => {
    void onIdle($, s).catch(() => undefined)
  })
}

// A prompt or a finished turn: the quiet clock restarts and the band goes away.
async function touch($: EngineInterface, s: Bridge): Promise<void> {
  if (s.isEnded) return
  s.lastActivityAt = await $.clock.now()
  armIdle($, s, s.idleMs)
  redraw($)
}

function idleMsOf(option: unknown): number {
  const minutes =
    typeof option === 'number' && Number.isFinite(option) && option >= MIN_IDLE_MINUTES && option <= MAX_IDLE_MINUTES
      ? option
      : DEFAULT_IDLE_MINUTES
  return minutes * MINUTE
}

async function initSession($: EngineInterface, s: Bridge, cwd: string): Promise<void> {
  s.cwd = cwd
  s.rootFor = undefined
  await resolveRoot($, s)
  const sid = await $.session.id()
  const ring = ringFor(s, sid)
  await ensureLoaded($, s, ring)

  const prior = await readPrior($, s)
  s.foldedPending = prior.pending
  const now = await $.clock.now()
  const turns = [...prior.rows, ...ring.entries.map(entry => entry.row)].filter(row => row.kind === 'turn')
  const lastTurn = newestWith(turns, () => true)
  const lastAt = lastTurn === undefined ? Number.NaN : Date.parse(lastTurn.ts)
  s.lastActivityAt = Number.isFinite(lastAt) && lastAt <= now ? lastAt : now
  armIdle($, s, s.lastActivityAt + s.idleMs - now)
  renderStatus($, s)

  void refreshBand($, s).then(() => redraw($), () => undefined)
}

async function bounded($: EngineInterface, work: Promise<void>, ms: number): Promise<void> {
  let timer: Timer | undefined
  try {
    const timeout = new Promise<void>(resolve => {
      timer = $.clock.after(ms, () => resolve())
    })
    await Promise.race([work.catch(() => undefined), timeout])
  } finally {
    timer?.cancel()
  }
}

function resetSession(s: Bridge): void {
  s.turnId = ''
  s.goal = ''
  s.files = []
  s.todosDone = []
  s.prevCompleted = new Map()
}

export const register: Register = (on, options) => {
  const s: Bridge = {
    idleMs: idleMsOf(options.idleMinutes),
    cwd: undefined,
    root: undefined,
    rootFor: undefined,
    rings: new Map(),
    foldedPending: 0,
    foldedDropped: 0,
    turnId: '',
    goal: '',
    files: [],
    todosDone: [],
    prevCompleted: new Map(),
    compactSeq: 0,
    lastActivityAt: undefined,
    idleTimer: undefined,
    bandLine: undefined,
    bandBusy: false,
    gitInFlight: false,
    isEnded: false,
  }

  on('session.start', async ($, e, next) => {
    try {
      s.isEnded = false
      // A hung file system must not hold the session start: the init carries on
      // in the background and the status line follows when it lands.
      await bounded($, initSession($, s, e.cwd), INIT_TIMEOUT_MS)
    } catch {
      // Never surface a failure from setup.
    }
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    try {
      // A prompt the person did not type (a notification) is not them being back.
      if (e.isMeta !== true) void touch($, s).catch(() => undefined)
    } catch {
      // never surface
    }
    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    try {
      // The goal and the per-turn state follow the main loop only.
      if (e.agentId === undefined) {
        s.turnId = e.turnId
        s.files = []
        s.todosDone = []
        const goal = clean(e.text, GOAL_CHARS)
        if (goal !== '') s.goal = goal
      }
    } catch {
      // never surface
    }
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    const result = await next(e)
    try {
      void observeTool($, s, e, result).catch(() => undefined)
    } catch {
      // never surface
    }
    return result
  })

  on('turn.complete', async ($, e, next) => {
    try {
      if (e.agentId === undefined && !s.isEnded) {
        void captureTurn($, s, e).catch(() => undefined)
        void touch($, s).catch(() => undefined)
      }
    } catch {
      // never surface
    }
    return next(e)
  })

  on('session.compact', async ($, e, next) => {
    const result = await next(e)
    try {
      if (e.agentId === undefined && !s.isEnded && result.skip === undefined) {
        void captureCompact($, s, e.trigger).catch(() => undefined)
      }
    } catch {
      // never surface
    }
    return result
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    // The band is drawn above whatever the rest draws, never instead of it.
    const inner = await next(e)
    try {
      const line = s.bandLine
      if (e.props.hasSurvey || s.isEnded || line === undefined || s.lastActivityAt === undefined) {
        return inner
      }
      const now = await $.clock.now()
      if (now - s.lastActivityAt < s.idleMs) return inner
      const { Box, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="column">
          <Text dimColor wrap="truncate-end">
            {line}
          </Text>
          {inner}
        </Box>
      ) as RenderElement
    } catch {
      return inner
    }
  })

  on('session.end', async ($, e, next) => {
    // /clear fires session.end with reason 'clear' but the process goes on and
    // no session.start follows: record the end, then keep everything running.
    // Every other reason is a real end: cancel everything.
    try {
      if (!s.isEnded) {
        const ring = s.rings.get(e.sessionId)
        if (ring !== undefined && ring.entries.length > 0) {
          await append($, s, {
            kind: 'end',
            sid: e.sessionId,
            turnId: s.turnId,
            disc: e.reason,
            goal: s.goal,
            files: [...s.files],
            intended: null,
          })
          await boundedFlush($, s, ring)
        }
        if (e.reason === 'clear') {
          // Fold the closed session into the counters; keep it if it is unsaved.
          if (ring !== undefined && !ring.dirty && !ring.flushing && !ring.failed) {
            for (const entry of ring.entries) if (entry.row.state === 'pending') s.foldedPending += 1
            s.foldedDropped += ring.dropped
            s.rings.delete(e.sessionId)
          }
          resetSession(s)
          renderStatus($, s)
        } else {
          s.isEnded = true
          s.idleTimer?.cancel()
          s.idleTimer = undefined
          $.ui.status(undefined)
        }
      }
    } catch {
      // never surface
    }
    return next(e)
  })
}
