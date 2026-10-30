import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine, MockClock } from 'claude-code/testing'

import {
  STATUS_DEBOUNCE_MS,
  commit,
  familyOf,
  flushAtEnd,
  flushSegments,
  initSession,
  limits,
  newLedger,
  parseConfig,
  recordSpawn,
  summarize,
  toBindingFields,
} from './register'

const T0 = 1_792_000_000_000
// What the mocked `$.session.root()` answers, and where mocked real paths land.
const ROOT = '/proj'
const DEFAULT_DIR = '.control-tower/state/route-ledger'
const FILE = `${DEFAULT_DIR}/sess-1.jsonl`
const SCHEMA = 'dopemux.route_ledger.receipt.v1'
const RFC3339 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/

const COMMON_KEYS = ['schema_version', 'kind', 'seq', 'session_id', 'recorded_at', 'agent_id']
const KEYS: Record<string, string[]> = {
  agent_request: [
    ...COMMON_KEYS,
    'tool_use_id',
    'requested_model',
    'requested_effort',
    'subagent_type',
    'description',
    'pinned',
    'inherits',
    'spawned_agent_id',
    'resolved_model',
    'binding_fields',
  ],
  step_observed: [
    ...COMMON_KEYS,
    'turn_id',
    'step_index',
    'requested_model',
    'requested_effort',
    'observed_model',
    'match',
    'usage',
    'binding_fields',
  ],
  advisor_call: [...COMMON_KEYS, 'advisor_use_id', 'started_at', 'ended_at', 'loop'],
}
const BINDING_KEYS = [
  'effort_observed',
  'effort_requested',
  'independence_class',
  'provider_attested_model',
  'response_claimed_model',
  'selection',
]

type Receipt = Record<string, any>
type ServerUse = { id: string; name: string; input: unknown; startedAt: number; endedAt?: number }

declare const console: { log: (...args: unknown[]) => void }
type StepInput = { turnId: string; index: number; model: string; effort?: string; agentId?: string }
type Usage = {
  model: string
  input_tokens: number
  output_tokens: number
  cache_read_input_tokens: number
  cache_creation_input_tokens: number
}

const USAGE: Usage = {
  model: 'claude-sonnet-5-5',
  input_tokens: 10,
  output_tokens: 20,
  cache_read_input_tokens: 30,
  cache_creation_input_tokens: 40,
}

type StatOverride =
  | 'missing'
  | { kind?: 'file' | 'dir' | 'other'; isLink?: boolean; realPath?: string }

type Opts = {
  dirs?: string[]
  files?: Record<string, string>
  sessionId?: string
  // The receiptDir the test configures (the default when left out).
  dir?: string
  // 'broken': `$.clock.now()` is refused beneath the plugin.
  clock?: 'mock' | 'broken'
}

// Everything beneath the plugin is mocked here: the clock, the file system (in
// memory, every write recorded), the session id, the toast, and the Agent
// tool, the spawn and the model step the plugin only observes.
function harness($: Engine, on: On, opts: Opts = {}) {
  let clock: MockClock
  if (opts.clock === 'broken') {
    on('clock.now', () => ({ deny: 'clock gone' }))
    clock = {
      settle: async () => {
        for (let i = 0; i < 100; i++) await Promise.resolve()
      },
    } as MockClock
  } else {
    clock = mock.clock(on, { now: T0 })
  }
  // The engine hands the plugin's file calls to the hooks beneath as absolute
  // paths under the session's directory. The mocked file system keeps them
  // relative to it, learned from the first path that names a known directory.
  const dir = opts.dir ?? DEFAULT_DIR
  let root: string | undefined
  const rel = (path: string): string => {
    if (root === undefined) {
      for (const known of ['.control-tower/state', dir]) {
        const i = path.indexOf(`/${known}`)
        const end = i + 1 + known.length
        if (i >= 0 && (end === path.length || path[end] === '/')) {
          root = path.slice(0, i)
          break
        }
      }
    }
    if (root !== undefined && path === root) return '.'
    return root !== undefined && path.startsWith(`${root}/`) ? path.slice(root.length + 1) : path
  }
  const isDir = (path: string): boolean =>
    path === '.' ||
    path === '/' ||
    world.dirs.has(path) ||
    [...world.dirs].some(dir => dir.startsWith(`${path}/`)) ||
    [...world.files.keys()].some(file => file.startsWith(`${path}/`))
  const world = {
    clock,
    files: new Map<string, string>(Object.entries(opts.files ?? {})),
    dirs: new Set<string>(opts.dirs ?? ['.control-tower/state']),
    writes: [] as { path: string; text: string }[],
    failWrites: false,
    // The next N writes are refused, then writes work again.
    failNext: 0,
    // Files that are listed but cannot be read (over 4 MiB, removed since).
    unreadable: new Set<string>(),
    // The session id `$.session.id()` answers; a test may change it.
    sessionId: opts.sessionId ?? 'sess-1',
    // Where the project root really lands (a symlinked root differs from ROOT).
    rootReal: undefined as string | undefined,
    // Per-path answers of `$.fs.stat`, keyed by the path as the mod spells it.
    stats: new Map<string, StatOverride>(),
    failStat: false,
    statCalls: [] as { path: string; resolve: boolean }[],
    ends: 0,
    toasts: [] as string[],
    toastTimeouts: [] as (number | undefined)[],
    statuses: [] as (string | undefined)[],
    registered: [] as string[],
    // Command names the engine refuses to register (a built-in collision).
    refused: new Set<string>(),
    calls: [] as Receipt[],
    spawns: [] as Receipt[],
    stepInputs: [] as Receipt[],
    // What the next model step answers; the test sets it before each step.
    usage: USAGE as Usage | null,
    serverToolUses: undefined as ServerUse[] | undefined,
    spawnAnswer: { model: 'claude-sonnet-5-5', agentId: 'agent-7' } as Receipt,
  }

  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.end', (_, e) => {
    world.ends += 1
    return { sessionId: e.sessionId }
  })
  on('session.id', () => ({ value: world.sessionId }))
  on('session.root', () => ({ value: ROOT }))
  on('ui.toast', (_, e) => {
    world.toasts.push(e.text)
    world.toastTimeouts.push(e.timeoutMs)
    return { value: undefined }
  })
  on('ui.status', (_, e) => {
    world.statuses.push(e.text)
    return { value: undefined }
  })
  on('command.register', (_, e) => {
    if (world.refused.has(e.name)) return { deny: `${e.name} is a built-in name` }
    world.registered.push(e.name)
    return { value: { command: e.name } }
  })
  on('fs.write', (_, e) => {
    const path = rel(e.path)
    world.writes.push({ path, text: e.text })
    if (world.failNext > 0) {
      world.failNext -= 1
      return { deny: 'disk full' }
    }
    if (world.failWrites) return { deny: 'disk full' }
    world.files.set(path, e.text)
    return { value: undefined }
  })
  on('fs.read', (_, e) => {
    const text = world.files.get(rel(e.path))
    if (world.unreadable.has(rel(e.path))) return { deny: `EFBIG ${e.path}` }
    return text === undefined ? { deny: `ENOENT ${e.path}` } : { value: text }
  })
  on('fs.stat', (_, e) => {
    const path = rel(e.path).replace(/(.)\/+$/, '$1')
    world.statCalls.push({ path, resolve: e.resolve })
    if (world.failStat) return { deny: 'EIO' }
    const override = world.stats.get(path)
    if (override === 'missing') return { deny: `ENOENT ${path}` }
    const isFile = world.files.has(path)
    if (!isFile && path !== ROOT && !isDir(path) && override === undefined) return { deny: `ENOENT ${path}` }
    const realRoot = world.rootReal ?? ROOT
    const real = path === ROOT ? realRoot : path.startsWith('/') ? path : path === '.' ? realRoot : `${realRoot}/${path}`
    return {
      value: {
        kind: isFile ? ('file' as const) : ('dir' as const),
        size: 1,
        mtimeMs: 0,
        isLink: false,
        ...(e.resolve ? { realPath: real } : {}),
        ...override,
      },
    }
  })
  on('fs.exists', (_, e) => {
    const path = rel(e.path)
    return { value: world.dirs.has(path) || world.files.has(path) }
  })
  on('fs.list', (_, e) => {
    const prefix = `${rel(e.path).replace(/\/+$/, '')}/`
    const entries = [...world.files.keys()]
      .filter(path => path.startsWith(prefix) && !path.slice(prefix.length).includes('/'))
      .map(path => ({
        name: path.slice(prefix.length),
        kind: 'file' as const,
        size: 1,
        mtimeMs: 0,
        isLink: false,
      }))
    return { value: entries }
  })
  on('tool.call', (_, e) => {
    world.calls.push(e as Receipt)
    return { result: { status: 'ok' }, text: 'done', ref: 0 }
  })
  on('agent.spawn', (_, e) => {
    world.spawns.push(e as Receipt)
    return world.spawnAnswer as never
  })
  on('turn.step', async function* (_, e) {
    world.stepInputs.push(e as Receipt)
    yield { kind: 'text', index: 0, text: 'hello' }
    yield { kind: 'text', index: 0, text: ' world' }
    return {
      turnId: e.turnId,
      index: e.index,
      answer: 'hello world',
      toolUses: [],
      ...(world.serverToolUses === undefined ? {} : { serverToolUses: world.serverToolUses }),
      stopReason: 'end_turn' as const,
      usage: world.usage,
    }
  })

  const lines = (path: string): Receipt[] => {
    const text = world.files.get(path)
    if (text === undefined) return []
    return text
      .split('\n')
      .filter(line => line !== '')
      .map(line => JSON.parse(line))
  }

  return {
    world,
    lines,
    receipts: () => lines(FILE),
    // Receipts printed for the offline jsonschema check against receipt.schema.json.
    sample() {
      for (const receipt of lines(FILE)) console.log(`RECEIPT-SAMPLE ${JSON.stringify(receipt)}`)
    },
    async start() {
      await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
      await clock.settle()
    },
    // The last status text the plugin pinned (undefined when cleared or never set).
    status: () => world.statuses[world.statuses.length - 1],
    async run(command: string, args = '') {
      return $.command.run({
        command,
        args,
        origin: { kind: 'composer' },
        presentation: { isFullscreen: false, columns: 80 },
      })
    },
    async settleStatus() {
      await clock.advance(STATUS_DEBOUNCE_MS)
    },
    async end(reason: 'clear' | 'other' = 'other') {
      const result = await $.session.end({ reason, sessionId: 'sess-1', resume: { sessionId: 'sess-1' } as never })
      await clock.settle()
      return result
    },
    async agent(args: Receipt = {}) {
      const before = world.calls.length
      const result = await $.tool.call({
        tool: 'Agent',
        description: 'Write the tests',
        prompt: 'SECRET-PROMPT-DO-NOT-LOG',
        ...args,
      } as never)
      await clock.settle()
      return { result, seen: world.calls.slice(before), id: world.calls[world.calls.length - 1]?.tool_use_id as string }
    },
    async spawn(toolUseId: string | undefined) {
      const result = await $.agent.spawn({
        prompt: 'SECRET-PROMPT-DO-NOT-LOG',
        description: 'Write the tests',
        ...(toolUseId === undefined ? {} : { tool_use_id: toolUseId }),
      } as never)
      await clock.settle()
      return result
    },
    async step(input: StepInput) {
      const stream = $.turn.step({ messageCount: 1, ...input } as never)
      const chunks: unknown[] = []
      for (;;) {
        const next = await stream.next()
        if (next.done) {
          await clock.settle()
          return { chunks, result: next.value as Receipt }
        }
        chunks.push(next.value)
      }
    },
    // No write may land anywhere but under `dir`.
    expectWritesUnder(dir: string) {
      for (const write of world.writes) {
        expect(write.path.startsWith(`${dir}/`)).toBe(true)
        expect(write.path.slice(dir.length + 1).includes('/')).toBe(false)
      }
    },
  }
}

const STEP: StepInput = { turnId: 'turn-1', index: 0, model: 'claude-sonnet-5-5' }

// ---------------------------------------------------------------- Agent calls

test('a pinned Agent call is recorded and passed on unchanged', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { result, seen, id } = await h.agent({
    subagent_type: 'general-purpose',
    model: 'sonnet',
    effort: 'high',
  })

  expect(seen).toHaveLength(1)
  expect(seen[0]).toEqual({
    tool: 'Agent',
    description: 'Write the tests',
    prompt: 'SECRET-PROMPT-DO-NOT-LOG',
    subagent_type: 'general-purpose',
    model: 'sonnet',
    effort: 'high',
    tool_use_id: id,
  })
  expect(result).toEqual({ result: { status: 'ok' }, text: 'done', ref: 0 })
  expect(h.world.toasts).toHaveLength(0)

  const receipt = h.receipts()[0]!
  expect(h.receipts()).toHaveLength(1)
  expect(receipt).toEqual({
    schema_version: SCHEMA,
    kind: 'agent_request',
    seq: 0,
    session_id: 'sess-1',
    recorded_at: new Date(T0).toISOString(),
    agent_id: null,
    tool_use_id: id,
    requested_model: 'sonnet',
    requested_effort: 'high',
    subagent_type: 'general-purpose',
    // recordDescription is off by default: the key stays, the text is not kept.
    description: '',
    pinned: true,
    inherits: false,
    spawned_agent_id: null,
    resolved_model: null,
    binding_fields: {
      selection: { runner: 'claude-code-agent', model: 'sonnet', effort: 'high' },
      effort_requested: 'high',
      effort_observed: 'UNKNOWN',
      response_claimed_model: 'UNKNOWN',
      provider_attested_model: 'UNKNOWN',
      independence_class: 'UNKNOWN',
    },
  })
  // The prompt never reaches a receipt.
  expect(h.world.files.get(FILE)?.includes('SECRET-PROMPT')).toBe(false)
  h.expectWritesUnder(DEFAULT_DIR)
})

test('an unpinned Agent call toasts once, naming the type and the short id but not the description or the prompt', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { seen, id } = await h.agent({ subagent_type: 'Explore', description: 'Map the repo' })

  expect(seen).toHaveLength(1)
  expect(h.world.toasts).toHaveLength(1)
  expect(h.world.toasts[0]!.includes('Explore')).toBe(true)
  expect(h.world.toasts[0]!.includes(id.slice(0, 8))).toBe(true)
  expect(h.world.toasts[0]!.includes('Map the repo')).toBe(false)
  expect(h.world.toasts[0]!.includes('SECRET-PROMPT')).toBe(false)
  // The host already names the plugin; a leading `route-ledger:` would print twice.
  expect(h.world.toasts[0]).not.toMatch(/^route-ledger:/)
  // An unset timeout falls back to the host default of 4 s, which is easy to miss.
  expect(h.world.toastTimeouts[0]).toBeGreaterThan(4000)

  const receipt = h.receipts()[0]!
  expect(receipt.pinned).toBe(false)
  expect(receipt.inherits).toBe(false)
  expect(receipt.requested_model).toBe(null)
  expect(receipt.requested_effort).toBe(null)
  expect(receipt.binding_fields.selection.model).toBe('UNKNOWN')
  expect(receipt.binding_fields.selection.effort).toBe('UNKNOWN')
  h.sample()
})

test('a fork with no model inherits: recorded as inherits, not unpinned, no toast', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { seen } = await h.agent({ subagent_type: 'fork' })

  expect(seen).toHaveLength(1)
  expect(h.world.toasts).toHaveLength(0)
  const receipt = h.receipts()[0]!
  expect(receipt.pinned).toBe(false)
  expect(receipt.inherits).toBe(true)
  expect(receipt.requested_model).toBe(null)
  h.sample()
})

test('unpinnedAgent off records but stays silent', { options: { unpinnedAgent: 'off' } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { seen } = await h.agent({ subagent_type: 'Explore' })

  expect(seen).toHaveLength(1)
  expect(h.world.toasts).toHaveLength(0)
  expect(h.receipts()).toHaveLength(1)
  expect(h.receipts()[0]!.pinned).toBe(false)
})

test('a long description is cut to 80 characters when recordDescription is on', { options: { recordDescription: true } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'haiku', description: 'x'.repeat(200) })
  expect(h.receipts()[0]!.description).toBe('x'.repeat(80))
})

test('next runs once with e unchanged when the write fails, and the next receipt heals the file', { options: { recordDescription: true } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.failWrites = true
  const first = await h.agent({ model: 'sonnet', description: 'first' })

  expect(first.seen).toHaveLength(1)
  expect(first.seen[0]).toMatchObject({ tool: 'Agent', description: 'first', model: 'sonnet' })
  expect(first.result).toEqual({ result: { status: 'ok' }, text: 'done', ref: 0 })
  expect(h.world.files.has(FILE)).toBe(false)
  // One attempt for the one receipt: no tight retry loop.
  expect(h.world.writes).toHaveLength(1)

  h.world.failWrites = false
  const second = await h.agent({ model: 'opus', description: 'second' })
  expect(second.seen).toHaveLength(1)
  const receipts = h.receipts()
  expect(receipts.map(r => r.seq)).toEqual([0, 1])
  expect(receipts.map(r => r.description)).toEqual(['first', 'second'])
})

test('next runs once with e unchanged when the clock fails', async ($, on) => {
  const h = harness($, on, { clock: 'broken' })
  await h.start()
  const { seen, result } = await h.agent({ model: 'sonnet' })
  expect(seen).toHaveLength(1)
  expect(result).toEqual({ result: { status: 'ok' }, text: 'done', ref: 0 })
})

// ------------------------------------------------------------ agent.spawn join

test('agent.spawn joins tool_use_id to the spawned agent and resolved model, and passes through', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const a = await h.agent({ model: 'haiku', description: 'same words' })
  const b = await h.agent({ model: 'opus', description: 'same words' })
  // The later call spawns: only its own receipt may be joined, not the first
  // unjoined one (no correlation by order or by description).
  const answer = await h.spawn(b.id)

  expect(answer).toEqual({ model: 'claude-sonnet-5-5', agentId: 'agent-7' })
  expect(h.world.spawns).toHaveLength(1)
  expect(h.world.spawns[0]).toEqual({
    prompt: 'SECRET-PROMPT-DO-NOT-LOG',
    description: 'Write the tests',
    tool_use_id: b.id,
  })

  const first = h.receipts()[0]!
  const second = h.receipts()[1]!
  expect(first.tool_use_id).toBe(a.id)
  expect(first.spawned_agent_id).toBe(null)
  expect(first.resolved_model).toBe(null)
  expect(second.tool_use_id).toBe(b.id)
  expect(second.spawned_agent_id).toBe('agent-7')
  expect(second.resolved_model).toBe('claude-sonnet-5-5')
  expect(h.receipts()).toHaveLength(2)
  h.sample()
})

test('agent.spawn without a tool_use_id, or a refused spawn, joins nothing', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'haiku' })
  await h.spawn(undefined)
  h.world.spawnAnswer = { deny: 'no' }
  const refused = await h.spawn(h.world.calls[0]!.tool_use_id)

  expect(refused).toEqual({ deny: 'no' })
  expect(h.receipts()[0]!.spawned_agent_id).toBe(null)
})

// ------------------------------------------------------------------ turn.step

test('turn.step passes chunks and result through and records requested versus observed', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { chunks, result } = await h.step({ ...STEP, effort: 'high' })

  expect(chunks).toEqual([
    { kind: 'text', index: 0, text: 'hello' },
    { kind: 'text', index: 0, text: ' world' },
  ])
  expect(result).toEqual({
    turnId: 'turn-1',
    index: 0,
    answer: 'hello world',
    toolUses: [],
    stopReason: 'end_turn',
    usage: USAGE,
  })
  // The request reached the engine as resolved, unrewritten.
  expect(h.world.stepInputs[0]).toMatchObject({ model: 'claude-sonnet-5-5', effort: 'high' })

  const receipt = h.receipts()[0]!
  expect(receipt).toEqual({
    schema_version: SCHEMA,
    kind: 'step_observed',
    seq: 0,
    session_id: 'sess-1',
    recorded_at: new Date(T0).toISOString(),
    agent_id: null,
    turn_id: 'turn-1',
    step_index: 0,
    requested_model: 'claude-sonnet-5-5',
    requested_effort: 'high',
    observed_model: 'claude-sonnet-5-5',
    match: true,
    usage: {
      input_tokens: 10,
      output_tokens: 20,
      cache_read_input_tokens: 30,
      cache_creation_input_tokens: 40,
    },
    binding_fields: {
      selection: { runner: 'claude-code-agent', model: 'claude-sonnet-5-5', effort: 'high' },
      effort_requested: 'high',
      effort_observed: 'UNKNOWN',
      response_claimed_model: 'claude-sonnet-5-5',
      provider_attested_model: 'UNKNOWN',
      independence_class: 'UNKNOWN',
    },
  })
})

test('a step whose observed model differs records match false; an agent step carries its agent id', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.usage = { ...USAGE, model: 'claude-haiku-4-5' }
  await h.step({ ...STEP, index: 1, agentId: 'agent-7' })

  const receipt = h.receipts()[0]!
  expect(receipt.agent_id).toBe('agent-7')
  expect(receipt.step_index).toBe(1)
  expect(receipt.requested_effort).toBe(null)
  expect(receipt.observed_model).toBe('claude-haiku-4-5')
  expect(receipt.match).toBe(false)
  expect(receipt.binding_fields.response_claimed_model).toBe('claude-haiku-4-5')
  expect(receipt.binding_fields.selection.effort).toBe('UNKNOWN')
  h.sample()
})

test('a dated observed id still matches its undated request; a bare alias matches its family', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.usage = { ...USAGE, model: 'claude-sonnet-5-5-20261001' }
  await h.step(STEP)
  h.world.usage = { ...USAGE, model: 'claude-sonnet-5-5' }
  await h.step({ ...STEP, index: 1, model: 'sonnet' })
  h.world.usage = { ...USAGE, model: 'claude-sonnet-5-6' }
  await h.step({ ...STEP, index: 2 })

  expect(h.receipts().map(r => r.match)).toEqual([true, true, false])
})

test('null usage and absent serverToolUses: UNKNOWN observed, match null, usage null, no advisor receipt', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.usage = null
  const { chunks, result } = await h.step(STEP)

  expect(chunks).toHaveLength(2)
  expect(result.usage).toBe(null)
  expect(result.serverToolUses).toBe(undefined)
  const receipts = h.receipts()
  expect(receipts).toHaveLength(1)
  expect(receipts[0]!.observed_model).toBe('UNKNOWN')
  expect(receipts[0]!.match).toBe(null)
  expect(receipts[0]!.usage).toBe(null)
  expect(receipts[0]!.binding_fields.response_claimed_model).toBe('UNKNOWN')
  h.sample()
})

test('advisor calls are counted once by server-tool-use id, split by loop', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [
    { id: 'srv-1', name: 'advisor', input: {}, startedAt: 5, endedAt: 9 },
    { id: 'srv-w', name: 'web_search', input: {}, startedAt: 5, endedAt: 6 },
  ]
  const main = await h.step(STEP)
  // The same id seen again (a replayed step) is not counted twice.
  await h.step({ ...STEP, index: 1 })
  h.world.serverToolUses = [{ id: 'srv-2', name: 'advisor', input: {}, startedAt: 7 }]
  await h.step({ ...STEP, index: 2, agentId: 'agent-7' })

  // The result goes back exactly as received, advisor entries included.
  expect(main.result.serverToolUses).toHaveLength(2)

  const advisors = h.receipts().filter(r => r.kind === 'advisor_call')
  expect(advisors.map(r => [r.advisor_use_id, r.loop, r.agent_id, r.started_at, r.ended_at])).toEqual([
    ['srv-1', 'main', null, 5, 9],
    ['srv-2', 'agent', 'agent-7', 7, null],
  ])
  expect(h.receipts().filter(r => r.kind === 'step_observed')).toHaveLength(3)
  // A duplicate consumes no seq: the numbering has no gap.
  expect(h.receipts().map(r => r.seq)).toEqual(h.receipts().map((_, i) => i))
  h.sample()
})

// ------------------------------------------------------------------- receipts

test('every receipt is a JSON line with exactly the schema keys, seq from 0 without gaps', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  const call = await h.agent({ model: 'sonnet', effort: 'low' })
  await h.spawn(call.id)
  await h.step(STEP)
  await h.agent({})

  const text = h.world.files.get(FILE)!
  expect(text.endsWith('\n')).toBe(true)
  const receipts = h.receipts()
  expect(receipts.map(r => r.kind)).toEqual([
    'agent_request',
    'step_observed',
    'advisor_call',
    'agent_request',
  ])
  receipts.forEach((receipt, i) => {
    expect(Object.keys(receipt).sort()).toEqual([...KEYS[receipt.kind]!].sort())
    expect(receipt.schema_version).toBe(SCHEMA)
    expect(receipt.seq).toBe(i)
    expect(receipt.session_id).toBe('sess-1')
    expect(RFC3339.test(receipt.recorded_at)).toBe(true)
    if (receipt.binding_fields !== undefined) {
      expect(Object.keys(receipt.binding_fields).sort()).toEqual(BINDING_KEYS)
      expect(Object.keys(receipt.binding_fields.selection).sort()).toEqual(['effort', 'model', 'runner'])
    }
  })
  h.sample()
})

test('a segment rolls at maxReceiptsPerFile into <sessionId>.<n>.jsonl', { options: { maxReceiptsPerFile: 50 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  for (let i = 0; i < 120; i++) await h.step({ ...STEP, index: i })

  const second = `${DEFAULT_DIR}/sess-1.1.jsonl`
  const third = `${DEFAULT_DIR}/sess-1.2.jsonl`
  expect(h.receipts()).toHaveLength(50)
  expect(h.lines(second)).toHaveLength(50)
  expect(h.lines(third)).toHaveLength(20)
  expect(h.world.files.has(`${DEFAULT_DIR}/sess-1.3.jsonl`)).toBe(false)
  expect(h.receipts()[0]!.seq).toBe(0)
  expect(h.lines(second)[0]!.seq).toBe(50)
  expect(h.lines(third)[19]!.seq).toBe(119)
  h.expectWritesUnder(DEFAULT_DIR)
})

test('after a reload the tallies are rebuilt from the receipt files: seq continues, advisor ids stay deduplicated', async ($, on) => {
  const old: Receipt[] = [
    { ...base('agent_request', 0), tool_use_id: 'toolu_old', requested_model: 'haiku', requested_effort: null, subagent_type: null, description: 'old', pinned: true, inherits: false, spawned_agent_id: 'agent-old', resolved_model: 'claude-haiku-4-5', binding_fields: bf('haiku') },
    { ...base('advisor_call', 1), advisor_use_id: 'srv-1', started_at: 1, ended_at: 2, loop: 'main' },
    { ...base('advisor_call', 2), advisor_use_id: 'srv-9', started_at: 1, ended_at: 2, loop: 'agent', agent_id: 'agent-old' },
  ]
  // The second segment holds the highest seq, as after a rollover.
  const files = {
    [FILE]: old.slice(0, 2).map(r => JSON.stringify(r)).join('\n') + '\n',
    [`${DEFAULT_DIR}/sess-1.1.jsonl`]: JSON.stringify(old[2]) + '\n',
    [`${DEFAULT_DIR}/other-session.jsonl`]: JSON.stringify({ ...base('advisor_call', 40), advisor_use_id: 'srv-x', started_at: 1, ended_at: 2, loop: 'main' }) + '\n',
  }
  const h = harness($, on, { files })
  await h.start()

  h.world.serverToolUses = [
    { id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 },
    { id: 'srv-9', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 },
    { id: 'srv-new', name: 'advisor', input: {}, startedAt: 3, endedAt: 4 },
  ]
  await h.step(STEP)

  // New receipts continue after the highest seq (2) and go to the last segment.
  const last = h.lines(`${DEFAULT_DIR}/sess-1.1.jsonl`)
  expect(last.map(r => r.seq)).toEqual([2, 3, 4])
  expect(last.map(r => r.advisor_use_id ?? r.kind)).toEqual(['srv-9', 'step_observed', 'srv-new'])
  expect(h.receipts()).toHaveLength(2)
})

function base(kind: string, seq: number): Receipt {
  return { schema_version: SCHEMA, kind, seq, session_id: 'sess-1', recorded_at: new Date(T0).toISOString(), agent_id: null }
}
function bf(model: string): Receipt {
  return {
    selection: { runner: 'claude-code-agent', model, effort: 'UNKNOWN' },
    effort_requested: 'UNKNOWN',
    effort_observed: 'UNKNOWN',
    response_claimed_model: 'UNKNOWN',
    provider_attested_model: 'UNKNOWN',
    independence_class: 'UNKNOWN',
  }
}

test('receipts are disabled when .control-tower/state is absent: nothing is written, calls still pass', async ($, on) => {
  const h = harness($, on, { dirs: [] })
  await h.start()
  const { seen } = await h.agent({ model: 'sonnet' })
  await h.step(STEP)

  expect(seen).toHaveLength(1)
  expect(h.world.writes).toHaveLength(0)
  expect(h.world.files.size).toBe(0)
})

test('a receiptDir with a .. segment disables receipts', { options: { receiptDir: '../evil' } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { seen } = await h.agent({ model: 'sonnet' })

  expect(seen).toHaveLength(1)
  expect(h.world.writes).toHaveLength(0)
})

test('a .. segment in the middle of receiptDir is refused too', { options: { receiptDir: 'a/../b' } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
})

test('an explicit receiptDir is written even without .control-tower/state, and nothing else is', { options: { receiptDir: 'out/ledger' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: 'out/ledger' })
  await h.start()
  await h.agent({ model: 'sonnet' })
  await h.step(STEP)

  expect(h.lines('out/ledger/sess-1.jsonl')).toHaveLength(2)
  h.expectWritesUnder('out/ledger')
})

test('the session id is sanitized into the file name', async ($, on) => {
  const h = harness($, on, { sessionId: 'a/b c..d' })
  await h.start()
  await h.agent({ model: 'sonnet' })

  expect([...h.world.files.keys()]).toEqual([`${DEFAULT_DIR}/a_b_c__d.jsonl`])
  expect(h.lines(`${DEFAULT_DIR}/a_b_c__d.jsonl`)[0]!.session_id).toBe('a/b c..d')
})

// ------------------------------------------------------------------ lifecycle

test('session.end clear is not an end; any other reason stops recording', { options: { recordDescription: true } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet', description: 'one' })
  await h.end('clear')
  await h.agent({ model: 'sonnet', description: 'two' })
  expect(h.receipts().map(r => r.description)).toEqual(['one', 'two'])

  await h.end('other')
  const { seen } = await h.agent({ model: 'sonnet', description: 'three' })
  expect(seen).toHaveLength(1)
  expect(h.receipts().map(r => r.description)).toEqual(['one', 'two'])
})

// ----------------------------------------------------------------- pure parts

test('toBindingFields maps only what the mod knows and leaves the rest UNKNOWN', async () => {
  expect(toBindingFields({ requestedModel: 'sonnet', requestedEffort: 'high', observedModel: 'claude-sonnet-5-5' })).toEqual({
    selection: { runner: 'claude-code-agent', model: 'sonnet', effort: 'high' },
    effort_requested: 'high',
    effort_observed: 'UNKNOWN',
    response_claimed_model: 'claude-sonnet-5-5',
    provider_attested_model: 'UNKNOWN',
    independence_class: 'UNKNOWN',
  })
  expect(toBindingFields({ requestedModel: null, requestedEffort: null, observedModel: null })).toEqual({
    selection: { runner: 'claude-code-agent', model: 'UNKNOWN', effort: 'UNKNOWN' },
    effort_requested: 'UNKNOWN',
    effort_observed: 'UNKNOWN',
    response_claimed_model: 'UNKNOWN',
    provider_attested_model: 'UNKNOWN',
    independence_class: 'UNKNOWN',
  })
  expect(toBindingFields({ requestedModel: 'x', requestedEffort: 3, observedModel: 'UNKNOWN' }).selection.effort).toBe('3')
})

test('familyOf follows the glyph rule', async () => {
  expect(familyOf('claude-sonnet-5-5')).toBe('S')
  expect(familyOf('Opus')).toBe('O')
  expect(familyOf('claude-haiku-4-5')).toBe('H')
  expect(familyOf('fable')).toBe('F')
  expect(familyOf('gpt-5')).toBe('other')
  expect(familyOf(null)).toBe('other')
  expect(familyOf(undefined)).toBe('other')
})

test('summarize counts each agent once, observed model first, falling back to the requested alias', async () => {
  const s = newLedger({})
  const agent = (key: string, requested: string | null, observed: string | null, pinned: boolean | null, inherits = false) => {
    s.agents[key] = { toolUseId: null, agentId: key, requestedModel: requested, observedModel: observed, pinned, inherits }
  }
  agent('a1', 'haiku', 'claude-sonnet-5-5', true)
  agent('a2', 'opus', null, true)
  agent('a3', null, 'claude-haiku-4-5', false)
  agent('a4', 'fable', null, true)
  agent('a5', null, null, false)
  agent('a6', null, null, false, true)
  agent('a7', null, 'claude-sonnet-5-5', null)
  s.advisorMain = 1
  s.advisorByAgent = { a1: 2, a3: 1 }
  s.receiptsFailed = 3
  s.receiptsEnabled = true
  s.receiptFile = 'x/y.jsonl'

  expect(summarize(s)).toEqual({
    agents: { S: 2, O: 1, H: 1, F: 1, other: 2 },
    unpinned: 2,
    advisorTotal: 4,
    advisorMain: 1,
    advisorByAgent: { a1: 2, a3: 1 },
    receiptsEnabled: true,
    receiptsFailed: 3,
    receiptFile: 'x/y.jsonl',
  })
})

test('parseConfig falls back to the default for a bad value and clamps the receipt cap', async () => {
  expect(parseConfig({})).toMatchObject({
    receiptDir: DEFAULT_DIR,
    unpinnedAgent: 'warn',
    childAdvisorBudget: 0,
    sessionAdvisorBudget: -1,
    maxReceiptsPerFile: 500,
  })
  expect(parseConfig({ maxReceiptsPerFile: 10 }).maxReceiptsPerFile).toBe(50)
  expect(parseConfig({ maxReceiptsPerFile: 99999 }).maxReceiptsPerFile).toBe(5000)
  expect(parseConfig({ maxReceiptsPerFile: 'abc' }).maxReceiptsPerFile).toBe(500)
  expect(parseConfig({ maxReceiptsPerFile: 1.5 }).maxReceiptsPerFile).toBe(500)
  expect(parseConfig({ unpinnedAgent: 'deny' }).unpinnedAgent).toBe('warn')
  expect(parseConfig({ unpinnedAgent: 'off' }).unpinnedAgent).toBe('off')
  expect(parseConfig({ childAdvisorBudget: 2.5 }).childAdvisorBudget).toBe(0)
  expect(parseConfig({ childAdvisorBudget: -4 }).childAdvisorBudget).toBe(-4)
  expect(parseConfig({ sessionAdvisorBudget: 3 }).sessionAdvisorBudget).toBe(3)
  expect(parseConfig({ sessionAdvisorBudget: 'x' }).sessionAdvisorBudget).toBe(-1)
  expect(parseConfig({ receiptDir: '' }).receiptDir).toBe(DEFAULT_DIR)
  expect(parseConfig({ receiptDir: 7 }).receiptDir).toBe(DEFAULT_DIR)
  expect(parseConfig({ receiptDir: ' out/x ' }).receiptDir).toBe('out/x')
})

test('a failed write is counted in the state, not thrown and not retried', async () => {
  const s = newLedger({})
  s.receiptsEnabled = true
  s.segments = [{ n: 0, path: 'd/x.jsonl', receipts: [{ seq: 0 } as never], bytes: 0, count: 1, evicted: false, linkChecked: false, dirty: true }]
  let attempts = 0
  const failing = {
    fs: {
      write: async () => {
        attempts += 1
        throw new Error('disk full')
      },
    },
  }

  await flushSegments(failing as never, s)
  expect(attempts).toBe(1)
  expect(s.receiptsFailed).toBe(1)
  expect(summarize(s).receiptsFailed).toBe(1)
})

// ----------------------------------------------------------- W02: status segment

const stepAs = (h: ReturnType<typeof harness>, agentId: string, model: string, index = 0) => {
  h.world.usage = { ...USAGE, model }
  return h.step({ ...STEP, index, agentId, model })
}

test('status shows `agents –` with no agents, set in session.start', async ($, on) => {
  const h = harness($, on)
  await h.start()
  expect(h.status()).toBe('agents –')
})

test('status counts agents in the fixed order S, O, H, F, ? and only non-zero', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await stepAs(h, 'a1', 'claude-haiku-4-5')
  await stepAs(h, 'a2', 'claude-sonnet-5-5')
  await stepAs(h, 'a3', 'claude-sonnet-5-5')
  await stepAs(h, 'a4', 'gpt-x')
  await stepAs(h, 'a5', 'claude-opus-5')
  await stepAs(h, 'a6', 'fable-1')
  await h.settleStatus()
  expect(h.status()).toBe('agents S×2 O×1 H×1 F×1 ?×1')

})

test('status with a single agent reads `agents S×1`', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1')
})

test('status shows advisor N only when N > 0, and N/B ⚠ once a budget is exceeded', { options: { sessionAdvisorBudget: 1, childAdvisorBudget: -1 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await h.step(STEP)
  await h.settleStatus()
  expect(h.status()).toBe('agents – · advisor 1')

  h.world.serverToolUses = [{ id: 'srv-2', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await h.step({ ...STEP, index: 1 })
  await h.settleStatus()
  expect(h.status()).toBe('agents – · advisor 2/1 ⚠')
})

test('a child over its budget shows its own count against its own budget, apart from the session total', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-7', 'claude-sonnet-5-5')
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1 · advisor 1 · child 1/0 ⚠')
})

test('the child segment names the worst child, and a session overage shows both segments', { options: { sessionAdvisorBudget: 1, childAdvisorBudget: 0 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-7', 'claude-sonnet-5-5')
  h.world.serverToolUses = [{ id: 'srv-2', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-7', 'claude-sonnet-5-5')
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1 · advisor 2/1 ⚠ · child 2/0 ⚠')
})

test('a clean agent after an over-budget one does not change the figures the status shows', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-7', 'claude-sonnet-5-5')
  h.world.serverToolUses = []
  await stepAs(h, 'agent-8', 'claude-haiku-5-5')
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1 H×1 · advisor 1 · child 1/0 ⚠')
})

test('status appends ledger off when receipts are disabled, and receipts ✗ after a failed write', async ($, on) => {
  const off = harness($, on, { dirs: [] })
  await off.start()
  expect(off.status()).toBe('agents – · ledger off')
})

test('status appends receipts ✗ when a receipt write failed', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.failWrites = true
  await h.agent({ model: 'sonnet' })
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1 · receipts ✗')
})

test('a burst of receipts is debounced into one status update', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const before = h.world.statuses.length
  for (let i = 0; i < 20; i++) await h.step({ ...STEP, index: i, agentId: `a${i}` })
  expect(h.world.statuses.length).toBe(before)
  // One millisecond short of the production constant: not redrawn yet.
  await h.world.clock.advance(STATUS_DEBOUNCE_MS - 1)
  expect(h.world.statuses.length).toBe(before)
  await h.world.clock.advance(1)
  expect(h.world.statuses.length).toBe(before + 1)
  expect(h.status()).toBe('agents S×20')
  await h.settleStatus()
  expect(h.world.statuses.length).toBe(before + 1)
})

test('session.end clear keeps the status; any other reason clears it', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'opus' })
  await h.settleStatus()
  await h.end('clear')
  expect(h.status()).toBe('agents O×1')
  await h.end('other')
  expect(h.status()).toBe(undefined)
  // A pending update does not bring the status back after the end.
  await h.settleStatus()
  expect(h.status()).toBe(undefined)
})

// ------------------------------------------------------------------ W02: toasts

test('a child over childAdvisorBudget toasts once per agent, names it, never claims prevention', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-1234567890', 'claude-sonnet-5-5')
  h.world.serverToolUses = [{ id: 'srv-2', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-1234567890', 'claude-sonnet-5-5', 1)
  expect(h.world.toasts).toHaveLength(1)
  const toast = h.world.toasts[0]!
  expect(toast.includes('agent-12')).toBe(true)
  expect(toast.includes('agent-1234567890')).toBe(false)
  expect(toast.includes('1')).toBe(true)
  expect(toast.includes('0')).toBe(true)
  expect(toast).toMatch(/cannot block/)
  expect(toast).not.toMatch(/prevented|blocked a/)
  expect(toast).not.toMatch(/^route-ledger:/)
  expect(h.world.toastTimeouts[0]).toBeGreaterThan(0)

  // Another agent crosses its own budget: its own toast.
  h.world.serverToolUses = [{ id: 'srv-3', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-other', 'claude-sonnet-5-5')
  expect(h.world.toasts).toHaveLength(2)
})

test('a budget of -1 never toasts for a child', { options: { childAdvisorBudget: -1 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-7', 'claude-sonnet-5-5')
  expect(h.world.toasts).toHaveLength(0)
})

test('the session total toasts once when it exceeds sessionAdvisorBudget', { options: { sessionAdvisorBudget: 1 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  for (const id of ['srv-1', 'srv-2', 'srv-3']) {
    h.world.serverToolUses = [{ id, name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
    await h.step({ ...STEP, index: Number(id.slice(-1)) })
  }
  expect(h.world.toasts).toHaveLength(1)
  expect(h.world.toasts[0]).toMatch(/session/)
  expect(h.world.toasts[0]).toMatch(/cannot block/)
  expect(h.world.toasts[0]).not.toMatch(/^route-ledger:/)
  expect(h.world.toastTimeouts[0]).toBeGreaterThan(0)
})

// ---------------------------------------------------------------- W02: commands

test('registers route-ledger then route, each on its own', async ($, on) => {
  const h = harness($, on)
  await h.start()
  expect(h.world.registered).toEqual(['route-ledger', 'route'])
})

test('a refused route registration leaves route-ledger and the status working', async ($, on) => {
  const h = harness($, on)
  h.world.refused.add('route')
  await h.start()
  expect(h.world.registered).toEqual(['route-ledger'])
  expect(h.status()).toBe('agents –')
  const answer = await h.run('route-ledger')
  expect(answer.text).toMatch(/model requested/)
})

test('a refused route-ledger registration does not stop route', async ($, on) => {
  const h = harness($, on)
  h.world.refused.add('route-ledger')
  await h.start()
  expect(h.world.registered).toEqual(['route'])
})

test('/route-ledger on an empty ledger prints the main row, UNKNOWN cells and the footer', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { text } = await h.run('route-ledger')
  const lines = text!.split('\n')
  expect(lines[0]).toBe('agent | runner | model requested | model observed | effort requested | match | advisor')
  expect(lines[1]).toBe('main | claude-code-agent | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 0')
  expect(text).toMatch(/response_claimed/)
  expect(text).toMatch(/effort observed is UNKNOWN/)
  expect(text).toMatch(/cannot block/)
})

test('/route-ledger on a mixed ledger has one row per loop', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.step({ ...STEP, effort: 'high' })
  const call = await h.agent({ model: 'haiku', effort: 'low', description: 'cheap' })
  await h.spawn(call.id)
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  h.world.usage = { ...USAGE, model: 'claude-haiku-4-5' }
  await h.step({ ...STEP, index: 1, agentId: 'agent-7', model: 'claude-haiku-4-5' })
  await h.agent({ subagent_type: 'Explore' })

  const rows = (await h.run('route-ledger')).text!.split('\n').slice(1, 4)
  expect(rows[0]).toBe('main | claude-code-agent | claude-sonnet-5-5 | claude-sonnet-5-5 | high | yes | 0')
  expect(rows[1]).toBe('agent-7 | claude-code-agent | haiku | claude-haiku-4-5 | low | yes | 1')
  expect(rows[2]).toMatch(/^pending:.* \| claude-code-agent \| UNKNOWN \| UNKNOWN \| UNKNOWN \| UNKNOWN \| 0$/)
})

test('a request that differs from what was observed shows match no', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const call = await h.agent({ model: 'opus' })
  await h.spawn(call.id)
  h.world.usage = { ...USAGE, model: 'claude-sonnet-5-5' }
  await h.step({ ...STEP, agentId: 'agent-7' })
  const rows = (await h.run('route-ledger')).text!.split('\n')
  expect(rows[2]).toBe('agent-7 | claude-code-agent | opus | claude-sonnet-5-5 | UNKNOWN | no | 0')
})

test('/route-ledger lists at most 60 loops then +N more', async ($, on) => {
  const h = harness($, on)
  await h.start()
  for (let i = 0; i < 75; i++) await h.step({ ...STEP, index: i, agentId: `a${i}` })
  const lines = (await h.run('route-ledger')).text!.split('\n')
  const rows = lines.filter(line => line.includes(' | claude-code-agent | '))
  expect(rows).toHaveLength(60)
  expect(rows[0]!.startsWith('main | ')).toBe(true)
  // main + 75 agents = 76 loops: 16 are cut.
  expect(lines).toContain('+16 more')
})

test('/route and /route-ledger answer the same text', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  const a = await h.run('route-ledger')
  const b = await h.run('route')
  expect(b.text).toBe(a.text)
  expect((await h.run('route', 'receipts')).text).toBe((await h.run('route-ledger', 'receipts')).text)
})

test('the receipts argument prints the file, counts and flags', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  await h.step(STEP)
  const { text } = await h.run('route-ledger', 'receipts')
  expect(text).toContain(FILE)
  expect(text).toMatch(/agent_request 1/)
  expect(text).toMatch(/step_observed 1/)
  expect(text).toMatch(/advisor_call 0/)
  expect(text).toMatch(/receiptsEnabled true/)
  expect(text).toMatch(/receiptsFailed 0/)
})

test('receipts argument with receipts disabled says so', async ($, on) => {
  const h = harness($, on, { dirs: [] })
  await h.start()
  const { text } = await h.run('route-ledger', 'receipts')
  expect(text).toMatch(/receiptsEnabled false/)
  expect(text).toMatch(/none/)
})

test('an unknown argument prints a usage line and changes nothing', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  const writes = h.world.writes.length
  const statuses = h.world.statuses.length
  const { text } = await h.run('route-ledger', 'frobnicate')
  expect(text!.includes('\n')).toBe(false)
  expect(text).toMatch(/Usage: \/route-ledger/)
  expect(h.world.writes.length).toBe(writes)
  expect(h.world.statuses.length).toBe(statuses)
  expect(h.receipts()).toHaveLength(1)
})

test('the command is read-only: running it writes nothing', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  const writes = h.world.writes.length
  await h.run('route-ledger')
  await h.run('route-ledger', 'receipts')
  await h.run('route', 'nope')
  expect(h.world.writes.length).toBe(writes)
})

test('nothing throws when the ledger is empty or odd input reaches summarize', async ($, on) => {
  const h = harness($, on)
  h.world.usage = null
  await h.start()
  await h.step(STEP)
  await h.step({ ...STEP, index: 1, agentId: 'a1' })
  await h.run('route-ledger')
  await h.settleStatus()
  expect(h.status()).toBe('agents ?×1')

  const s = newLedger({})
  s.agents['x'] = { toolUseId: null, agentId: null, requestedModel: 5 as never, observedModel: null, pinned: null, inherits: false }
  expect(() => summarize(s)).not.toThrow()
})

// ======================================================================= R5 repairs
//
// Test-only helpers: receipt literals as they sit in a file, and an in-memory
// `$` for the tests that drive the exported ledger functions directly.

function stepRec(seq: number, over: Receipt = {}): Receipt {
  return {
    ...base('step_observed', seq),
    turn_id: 'turn-x',
    step_index: seq,
    requested_model: 'claude-sonnet-5-5',
    requested_effort: 'high',
    observed_model: 'claude-sonnet-5-5',
    match: true,
    usage: null,
    binding_fields: bf('claude-sonnet-5-5'),
    ...over,
  }
}
function reqRec(seq: number, over: Receipt = {}): Receipt {
  return {
    ...base('agent_request', seq),
    tool_use_id: `toolu_${seq}`,
    requested_model: null,
    requested_effort: null,
    subagent_type: 'Explore',
    description: '',
    pinned: false,
    inherits: false,
    spawned_agent_id: null,
    resolved_model: null,
    binding_fields: bf('UNKNOWN'),
    ...over,
  }
}
function advRec(seq: number, id: string, over: Receipt = {}): Receipt {
  return { ...base('advisor_call', seq), advisor_use_id: id, started_at: 1, ended_at: 2, loop: 'main', ...over }
}
const jsonl = (receipts: Receipt[]): string => receipts.map(r => JSON.stringify(r)).join('\n') + '\n'
const asReceipt = (r: Receipt): never => r as never

function fakeEnv(init: Record<string, string> = {}) {
  const files = new Map<string, string>(Object.entries(init))
  const writes: string[] = []
  const flags = { failWrites: false, failNext: 0 }
  const $ = {
    fs: {
      write: async (path: string, text: string) => {
        writes.push(path)
        if (flags.failNext > 0) {
          flags.failNext -= 1
          throw new Error('disk full')
        }
        if (flags.failWrites) throw new Error('disk full')
        files.set(path, text)
      },
      read: async (path: string) => {
        const text = files.get(path)
        if (text === undefined) throw new Error('ENOENT')
        return text
      },
      list: async (dir: string) =>
        [...files.keys()]
          .filter(path => path.startsWith(`${dir}/`))
          .map(path => ({ name: path.slice(dir.length + 1), kind: 'file', size: 1, mtimeMs: 0, isLink: false })),
      exists: async () => true,
      stat: async (path: string, options?: { resolve: boolean }) => {
        if (path.endsWith('.jsonl') && !files.has(path)) throw new Error('ENOENT')
        const real = path.startsWith('/') ? path : `${ROOT}/${path}`
        return {
          kind: path.endsWith('.jsonl') ? 'file' : 'dir',
          size: 1,
          mtimeMs: 0,
          isLink: false,
          ...(options?.resolve === true ? { realPath: real } : {}),
        }
      },
    },
    session: { id: async () => 'sess-1', root: async () => ROOT },
    clock: { after: () => ({ cancel() {} }) },
    ui: { status() {}, toast() {} },
  }
  return { $: $ as never, files, writes, flags }
}

// A ledger as `initSession` leaves it for the default directory.
function readyLedger(options: Record<string, unknown> = {}) {
  const s = newLedger(options)
  s.isReady = true
  s.receiptsEnabled = true
  s.sessionId = 'sess-1'
  s.fileStem = 'sess-1'
  s.receiptDir = DEFAULT_DIR
  return s
}

// -------------------------------------------------------- D1 (N11): the main row

test('D1: the main row shows the last main step when receipts are disabled', async ($, on) => {
  const h = harness($, on, { dirs: [] })
  await h.start()
  await h.step({ ...STEP, effort: 'high' })

  expect(h.world.writes).toHaveLength(0)
  const rows = (await h.run('route-ledger')).text!.split('\n')
  expect(rows[1]).toBe('main | claude-code-agent | claude-sonnet-5-5 | claude-sonnet-5-5 | high | yes | 0')
})

test('D1: the main row is rebuilt on rehydrate from the receipt files', async ($, on) => {
  const files = {
    [FILE]: jsonl([stepRec(0, { requested_model: 'claude-opus-5', observed_model: 'claude-opus-5', requested_effort: 'max' })]),
    [`${DEFAULT_DIR}/sess-1.1.jsonl`]: jsonl([stepRec(1, { agent_id: 'agent-9' }), advRec(2, 'srv-1')]),
  }
  const h = harness($, on, { files })
  await h.start()
  const rows = (await h.run('route-ledger')).text!.split('\n')
  expect(rows[1]).toBe('main | claude-code-agent | claude-opus-5 | claude-opus-5 | max | yes | 1')
})

// ------------------------------------------------------- D2 (N12): empty strings

test('D2: an empty effort is no effort, and an empty advisor id is no advisor call', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet', effort: '' })
  h.world.serverToolUses = [{ id: '', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await h.step({ ...STEP, effort: '' })

  const receipts = h.receipts()
  expect(receipts.map(r => r.kind)).toEqual(['agent_request', 'step_observed'])
  for (const receipt of receipts) {
    expect(receipt.requested_effort).toBe(null)
    expect(receipt.binding_fields.selection.effort).toBe('UNKNOWN')
    expect(receipt.binding_fields.effort_requested).toBe('UNKNOWN')
  }
  h.sample()
})

test('D2: toBindingFields treats an empty effort as UNKNOWN', async () => {
  const fields = toBindingFields({ requestedModel: 'sonnet', requestedEffort: '', observedModel: null })
  expect(fields.selection.effort).toBe('UNKNOWN')
  expect(fields.effort_requested).toBe('UNKNOWN')
})

test('D2: no receipt carries an empty selection.effort, effort_requested or advisor_use_id', async ($, on) => {
  const h = harness($, on)
  await h.start()
  let n = 0
  for (const effort of ['', 'high']) {
    for (const id of ['', 'srv-ok']) {
      n += 1
      await h.agent({ model: 'sonnet', effort })
      h.world.serverToolUses = [{ id: `${id}${id === '' ? '' : n}`, name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
      await h.step({ ...STEP, index: n, effort })
    }
  }
  const receipts = h.receipts()
  expect(receipts.filter(r => r.kind === 'advisor_call')).toHaveLength(2)
  for (const receipt of receipts) {
    if (receipt.binding_fields !== undefined) {
      expect(receipt.binding_fields.selection.effort).not.toBe('')
      expect(receipt.binding_fields.effort_requested).not.toBe('')
      expect(receipt.requested_effort).not.toBe('')
    }
    if (receipt.kind === 'advisor_call') expect(receipt.advisor_use_id).not.toBe('')
  }
  h.sample()
})

// ----------------------------------------------- D3 (N13a): toast-once on reload

test('D3: a reload restores the toast-once state, so nothing toasts twice', { options: { sessionAdvisorBudget: 1 } }, async ($, on) => {
  const files = {
    [FILE]: jsonl([
      reqRec(0, { tool_use_id: 'toolu_old_unpinned' }),
      advRec(1, 'srv-a', { loop: 'agent', agent_id: 'agent-old' }),
      advRec(2, 'srv-b', { loop: 'agent', agent_id: 'agent-old' }),
    ]),
  }
  const h = harness($, on, { files })
  await h.start()

  // Another advisor call by the child and the session that were already over budget.
  h.world.serverToolUses = [{ id: 'srv-c', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-old', 'claude-sonnet-5-5')
  expect(h.world.toasts).toHaveLength(0)

  // The same unpinned call seen again does not toast; a new one still does.
  const again = await h.agent({ subagent_type: 'Explore', tool_use_id: 'toolu_old_unpinned' })
  expect(again.seen[0]!.tool_use_id).toBe('toolu_old_unpinned')
  expect(h.world.toasts).toHaveLength(0)
  await h.agent({ subagent_type: 'Explore' })
  expect(h.world.toasts).toHaveLength(1)
})

test('D3: a pinned call and a fork are not restored as toasted, a budget of -1 restores nothing', { options: { childAdvisorBudget: -1 } }, async ($, on) => {
  const files = {
    [FILE]: jsonl([
      reqRec(0, { tool_use_id: 'toolu_pinned', pinned: true, requested_model: 'haiku' }),
      reqRec(1, { tool_use_id: 'toolu_fork', subagent_type: 'fork', inherits: true }),
      advRec(2, 'srv-a', { loop: 'agent', agent_id: 'agent-old' }),
    ]),
  }
  const h = harness($, on, { files, })
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-b', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-old', 'claude-sonnet-5-5')
  expect(h.world.toasts).toHaveLength(0)
  // Not restored as toasted: an unpinned call under a pinned receipt's id would toast.
  await h.agent({ subagent_type: 'Explore', tool_use_id: 'toolu_pinned' })
  expect(h.world.toasts).toHaveLength(1)
})

// ------------------------------------------------------------ D4 (N4): final flush

test('D4: session.end makes one more awaited flush when the first leaves a dirty tail', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.failNext = 2
  await h.agent({ model: 'sonnet' })
  expect(h.world.files.has(FILE)).toBe(false)

  const result = await h.end('other')
  expect(result).toEqual({ sessionId: 'sess-1' })
  expect(h.world.ends).toBe(1)
  // write 1 at the record, write 2 at the end (refused), write 3 the one more attempt.
  expect(h.world.writes).toHaveLength(3)
  expect(h.receipts()).toHaveLength(1)
})

test('D4: when both final writes fail it is counted, not thrown and not retried further', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.failNext = 3
  await h.agent({ model: 'sonnet' })

  const result = await h.end('other')
  expect(result).toEqual({ sessionId: 'sess-1' })
  expect(h.world.ends).toBe(1)
  expect(h.world.writes).toHaveLength(3)
  expect(h.world.files.has(FILE)).toBe(false)
})

test('D4: flushAtEnd retries once, counts each failure and stops; a clean ledger writes nothing', async () => {
  const dirty = (): ReturnType<typeof readyLedger> => {
    const s = readyLedger()
    s.segments = [{ n: 0, path: FILE, receipts: [stepRec(0) as never], bytes: 10, count: 1, evicted: false, linkChecked: false, dirty: true }]
    return s
  }

  const failing = fakeEnv()
  failing.flags.failWrites = true
  const s1 = dirty()
  await flushAtEnd(failing.$, s1)
  expect(failing.writes).toHaveLength(2)
  expect(s1.receiptsFailed).toBe(2)
  expect(s1.segments[0]!.dirty).toBe(true)

  const healing = fakeEnv()
  healing.flags.failNext = 1
  const s2 = dirty()
  await flushAtEnd(healing.$, s2)
  expect(healing.writes).toHaveLength(2)
  expect(s2.receiptsFailed).toBe(1)
  expect(s2.segments[0]!.dirty).toBe(false)
  expect(healing.files.get(FILE)).toBe(JSON.stringify(stepRec(0)) + '\n')

  const clean = fakeEnv()
  const s3 = readyLedger()
  await flushAtEnd(clean.$, s3)
  expect(clean.writes).toHaveLength(0)
})

// ----------------------------------------------- D6 (N2): directory and file safety

const receiptsText = async (h: ReturnType<typeof harness>) => (await h.run('route-ledger', 'receipts')).text!

test('D6: a trailing slash on the default directory still requires .control-tower/state', { options: { receiptDir: '.control-tower/state/route-ledger/' } }, async ($, on) => {
  const h = harness($, on, { dirs: [] })
  await h.start()
  const { seen } = await h.agent({ model: 'sonnet' })
  expect(seen).toHaveLength(1)
  expect(h.world.writes).toHaveLength(0)
  expect(await receiptsText(h)).toMatch(/\.control-tower\/state does not exist/)
})

test('D6: a trailing slash on the default directory is written beside existing state', { options: { receiptDir: '.control-tower/state/route-ledger/' } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.receipts()).toHaveLength(1)
  h.expectWritesUnder(DEFAULT_DIR)
})

test('D6: a receipt directory that is a symbolic link disables receipts, with the reason', async ($, on) => {
  const h = harness($, on)
  h.world.stats.set(DEFAULT_DIR, { isLink: true, realPath: `${ROOT}/elsewhere` })
  await h.start()
  const { seen } = await h.agent({ model: 'sonnet' })
  expect(seen).toHaveLength(1)
  expect(h.world.writes).toHaveLength(0)
  const text = await receiptsText(h)
  expect(text).toMatch(/receiptsEnabled false/)
  expect(text).toMatch(/symbolic link/)
})

test('D6: a receipt directory that is not a directory disables receipts', async ($, on) => {
  const h = harness($, on)
  h.world.stats.set(DEFAULT_DIR, { kind: 'file' })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
  expect(await receiptsText(h)).toMatch(/not a directory/)
})

test('D6: a symbolic parent of a missing directory disables receipts', { options: { receiptDir: 'out/ledger' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: 'out/ledger' })
  h.world.stats.set('out', { isLink: true, realPath: '/elsewhere/out' })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
  expect(await receiptsText(h)).toMatch(/symbolic link/)
})

test('D6: a relative directory whose parent resolves outside the project root disables receipts', { options: { receiptDir: 'out/ledger' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: 'out/ledger' })
  // `out` is not itself a link here (a link higher up leads it elsewhere).
  h.world.stats.set('out', { realPath: '/elsewhere/out' })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
  expect(await receiptsText(h)).toMatch(/outside the project root/)
})

test('D6: an existing relative directory that lands outside the project root disables receipts', { options: { receiptDir: 'out/ledger' } }, async ($, on) => {
  const h = harness($, on, { dirs: ['out/ledger'], dir: 'out/ledger' })
  h.world.stats.set('out/ledger', { realPath: '/elsewhere/out/ledger' })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
  expect(await receiptsText(h)).toMatch(/outside the project root/)
})

test('D6: a relative directory that stays inside the project is written, root compared after resolving', { options: { receiptDir: 'out/ledger' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: 'out/ledger' })
  // The project root itself sits behind a link: both sides are resolved the same way.
  h.world.rootReal = '/private/proj'
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.lines('out/ledger/sess-1.jsonl')).toHaveLength(1)
  h.expectWritesUnder('out/ledger')
  expect(h.world.statCalls.some(call => call.path === ROOT && call.resolve)).toBe(true)
})

test('D6: a sibling that only shares the root as a name prefix is outside it', { options: { receiptDir: 'out/ledger' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: 'out/ledger' })
  h.world.stats.set('out', { realPath: `${ROOT}-other/out` })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
})

test('D6: an absolute directory is allowed by design', { options: { receiptDir: '/var/ledger-out' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: '/var/ledger-out' })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.lines('/var/ledger-out/sess-1.jsonl')).toHaveLength(1)
  h.expectWritesUnder('/var/ledger-out')
})

test('D6: an absolute directory that is itself a link is still refused', { options: { receiptDir: '/var/ledger-out' } }, async ($, on) => {
  const h = harness($, on, { dirs: [], dir: '/var/ledger-out' })
  h.world.stats.set('/var/ledger-out', { isLink: true })
  await h.start()
  await h.agent({ model: 'sonnet' })
  expect(h.world.writes).toHaveLength(0)
})

test('D6: a stat that rejects everywhere disables receipts and nothing throws', async ($, on) => {
  const h = harness($, on)
  h.world.failStat = true
  await h.start()
  const { seen, result } = await h.agent({ model: 'sonnet' })
  expect(seen).toHaveLength(1)
  expect(result).toEqual({ result: { status: 'ok' }, text: 'done', ref: 0 })
  expect(h.world.writes).toHaveLength(0)
  expect(await receiptsText(h)).toMatch(/could not be inspected/)
})

test('D6: a segment file that is a symbolic link is not written, receipts go off with a reason', async ($, on) => {
  const h = harness($, on)
  h.world.stats.set(FILE, { kind: 'file', isLink: true })
  await h.start()
  const first = await h.agent({ model: 'sonnet' })
  await h.settleStatus()
  await h.agent({ model: 'opus' })

  expect(first.seen).toHaveLength(1)
  expect(h.world.writes).toHaveLength(0)
  expect(h.status()).toMatch(/ledger off/)
  const text = await receiptsText(h)
  expect(text).toMatch(/receiptsEnabled false/)
  expect(text).toMatch(/sess-1\.jsonl is a symbolic link/)
})

test('D6: a segment file is checked once, before its first write only', async ($, on) => {
  const h = harness($, on)
  await h.start()
  for (let i = 0; i < 3; i++) await h.agent({ model: 'sonnet' })
  expect(h.world.writes.length).toBeGreaterThanOrEqual(3)
  expect(h.world.statCalls.filter(call => call.path === FILE)).toHaveLength(1)
})

// --------------------------------------------------- D7 (N3): bound the memory

test('D7: closed segments are evicted after a flush; the open one, the counts and the last main step stay', async () => {
  const s = readyLedger()
  s.config.maxReceiptsPerFile = 3
  const env = fakeEnv()
  for (let i = 0; i < 8; i++) {
    commit(env.$, s, asReceipt(stepRec(i, { agent_id: i === 0 ? null : `a${i}`, requested_model: `m${i}` })))
  }
  await s.chain

  expect(s.segments.map(g => g.receipts.length)).toEqual([0, 0, 2])
  expect(s.segments.map(g => g.evicted)).toEqual([true, true, false])
  expect(s.segments.map(g => g.count)).toEqual([3, 3, 2])
  expect(s.segments.every(g => g.bytes > 0)).toBe(true)
  expect(s.segments.map(g => g.path)).toEqual([FILE, `${DEFAULT_DIR}/sess-1.1.jsonl`, `${DEFAULT_DIR}/sess-1.2.jsonl`])
  expect(s.counts).toEqual({ agent_request: 0, step_observed: 8, advisor_call: 0 })
  expect(s.lastMain?.seq).toBe(0)
  // Everything was written before it left memory.
  expect(env.files.get(FILE)!.split('\n').filter(line => line !== '')).toHaveLength(3)

  // A closed segment is never written again.
  const before = env.writes.length
  commit(env.$, s, asReceipt(stepRec(8)))
  await s.chain
  expect(env.writes.slice(before)).toEqual([`${DEFAULT_DIR}/sess-1.2.jsonl`])
})

test('D7: the receipts command still counts every receipt once the closed segments are gone', { options: { maxReceiptsPerFile: 50 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  for (let i = 0; i < 120; i++) await h.step({ ...STEP, index: i })
  const text = await receiptsText(h)
  expect(text).toMatch(/step_observed 120/)
  expect(text).toMatch(/agent_request 0/)
})

test('D7: nothing evicts a dirty segment, and a healed one goes at the next flush', async () => {
  const s = readyLedger()
  s.config.maxReceiptsPerFile = 3
  const env = fakeEnv()
  env.flags.failWrites = true
  for (let i = 0; i < 5; i++) commit(env.$, s, asReceipt(stepRec(i)))
  await s.chain
  expect(s.segments.map(g => g.dirty)).toEqual([true, true])
  expect(s.segments.map(g => g.receipts.length)).toEqual([3, 2])
  expect(s.segments.map(g => g.evicted)).toEqual([false, false])

  env.flags.failWrites = false
  await flushSegments(env.$, s)
  expect(s.segments.map(g => g.receipts.length)).toEqual([0, 2])
  expect(s.segments.map(g => g.evicted)).toEqual([true, false])
  expect(env.files.get(FILE)!.split('\n').filter(line => line !== '')).toHaveLength(3)
})

test('D7: a segment holding an agent_request still awaiting its spawn join is kept until it is joined', async () => {
  const s = readyLedger()
  s.config.maxReceiptsPerFile = 2
  const env = fakeEnv()
  commit(env.$, s, asReceipt(reqRec(0, { tool_use_id: 'toolu_a', pinned: true, requested_model: 'haiku' })))
  for (let i = 1; i <= 4; i++) commit(env.$, s, asReceipt(stepRec(i)))
  await s.chain
  expect(s.segments.map(g => g.receipts.length)).toEqual([2, 0, 1])
  expect(s.segments.map(g => g.evicted)).toEqual([false, true, false])

  await recordSpawn(env.$, s, 'toolu_a', 'agent-1', 'claude-haiku-4-5')
  await s.chain
  expect(s.segments[0]!.evicted).toBe(true)
  expect(s.segments[0]!.receipts).toHaveLength(0)
  // The join was written whole before the segment left memory.
  const rewritten = env.files.get(FILE)!.split('\n').filter(line => line !== '').map(line => JSON.parse(line))
  expect(rewritten).toHaveLength(2)
  expect(rewritten[0].spawned_agent_id).toBe('agent-1')
  expect(rewritten[0].resolved_model).toBe('claude-haiku-4-5')
})

test('D7: rehydrate evicts each closed segment after tallying it and keeps the last one', async () => {
  const env = fakeEnv({
    [FILE]: jsonl([stepRec(0), stepRec(1, { agent_id: 'a1' }), advRec(2, 'srv-1')]),
    [`${DEFAULT_DIR}/sess-1.1.jsonl`]: jsonl([reqRec(3, { tool_use_id: 'toolu_unjoined' }), stepRec(4)]),
    [`${DEFAULT_DIR}/sess-1.2.jsonl`]: jsonl([stepRec(5), advRec(6, 'srv-2', { loop: 'agent', agent_id: 'a1' })]),
  })
  const s = newLedger({})
  await initSession(env.$, s)

  expect(s.receiptsEnabled).toBe(true)
  expect(s.segments.map(g => g.n)).toEqual([0, 1, 2])
  expect(s.segments.map(g => g.count)).toEqual([3, 2, 2])
  // The middle one still holds a request awaiting its join, so it stays.
  expect(s.segments.map(g => g.evicted)).toEqual([true, false, false])
  expect(s.segments[0]!.receipts).toHaveLength(0)
  expect(s.counts).toEqual({ agent_request: 1, step_observed: 4, advisor_call: 2 })
  expect(s.lastMain?.seq).toBe(5)
  expect(s.nextSeq).toBe(7)
  expect(env.writes).toHaveLength(0)
})

// ------------------------------------------------------ D8 (N5): after /clear

test('D8: after /clear a new session id means a new file and a fresh ledger', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  await h.step(STEP)
  await h.end('clear')

  h.world.sessionId = 'sess-2'
  await h.agent({ model: 'opus' })
  const next = h.lines(`${DEFAULT_DIR}/sess-2.jsonl`)
  expect(next).toHaveLength(1)
  expect(next[0]!.seq).toBe(0)
  expect(next[0]!.session_id).toBe('sess-2')
  // The pre-clear file is complete and untouched afterwards.
  expect(h.receipts().map(r => r.kind)).toEqual(['agent_request', 'step_observed'])

  const text = await receiptsText(h)
  expect(text).toMatch(/sess-2\.jsonl/)
  expect(text).toMatch(/agent_request 1, step_observed 0/)
  // The table restarts too: one agent, and the old main step is gone.
  const rows = (await h.run('route-ledger')).text!.split('\n')
  expect(rows[1]).toMatch(/^main \| claude-code-agent \| UNKNOWN \| UNKNOWN \| UNKNOWN \| UNKNOWN \| 0$/)
  expect(rows.filter(line => line.startsWith('pending:'))).toHaveLength(1)
})

test('D8: after /clear an unchanged session id rehydrates and continues the same file', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  await h.step(STEP)
  await h.end('clear')

  await h.agent({ model: 'opus' })
  expect(h.receipts().map(r => r.seq)).toEqual([0, 1, 2])
  expect(h.receipts().map(r => r.kind)).toEqual(['agent_request', 'step_observed', 'agent_request'])
  const text = await receiptsText(h)
  expect(text).toMatch(/agent_request 2, step_observed 1/)
  const rows = (await h.run('route-ledger')).text!.split('\n')
  expect(rows[1]).toBe('main | claude-code-agent | claude-sonnet-5-5 | claude-sonnet-5-5 | UNKNOWN | yes | 0')
})

test('D8: /clear writes a dirty tail before the ledger is reset', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.failWrites = true
  await h.agent({ model: 'sonnet' })
  expect(h.world.files.has(FILE)).toBe(false)
  h.world.failWrites = false
  await h.end('clear')
  expect(h.receipts()).toHaveLength(1)
})

test('D8: /clear keeps the status line, up to date, and a pending redraw does not show the reset ledger', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'sonnet' })
  // No settle: the redraw for this receipt is still pending when /clear arrives.
  await h.end('clear')
  expect(h.status()).toBe('agents S×1')
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1')
})

test('D8: a hook that follows /clear re-resolves the session id before it records', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.step(STEP)
  await h.end('clear')
  h.world.sessionId = 'sess-3'
  await h.step({ ...STEP, index: 1 })
  expect(h.lines(`${DEFAULT_DIR}/sess-3.jsonl`).map(r => r.step_index)).toEqual([1])
})

// ----------------------------------------------------- D9 (N9): the description

test('D9: by default the description is neither recorded nor toasted', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { id } = await h.agent({ subagent_type: 'Explore', description: 'Refactor the payroll module' })

  const receipt = h.receipts()[0]!
  expect(Object.keys(receipt)).toContain('description')
  expect(receipt.description).toBe('')
  expect(h.world.files.get(FILE)!.includes('payroll')).toBe(false)
  expect(h.world.toasts).toHaveLength(1)
  expect(h.world.toasts[0]!.includes('payroll')).toBe(false)
  expect(h.world.toasts[0]).toBe(`Agent call ${id.slice(0, 8)} (Explore) has no model pinned.`)
  h.sample()
})

test('D9: recordDescription on records the first 80 characters and toasts them', { options: { recordDescription: true } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ subagent_type: 'Explore', description: 'Map the repo' })
  await h.agent({ model: 'haiku', description: 'y'.repeat(120) })

  expect(h.receipts()[0]!.description).toBe('Map the repo')
  expect(h.receipts()[1]!.description).toBe('y'.repeat(80))
  expect(h.world.toasts).toHaveLength(1)
  expect(h.world.toasts[0]).toBe('Agent call "Map the repo" (Explore) has no model pinned.')
  h.sample()
})

test('D9: parseConfig takes a boolean recordDescription and falls back to false for anything else', async () => {
  expect(parseConfig({}).recordDescription).toBe(false)
  expect(parseConfig({ recordDescription: true }).recordDescription).toBe(true)
  expect(parseConfig({ recordDescription: false }).recordDescription).toBe(false)
  for (const bad of ['true', 'yes', 1, 0, null, undefined, {}, []]) {
    expect(parseConfig({ recordDescription: bad }).recordDescription).toBe(false)
  }
})

// ---------------------------------------------------- D10 (O1-O5): missing tests

test('a segment also rolls by bytes, before maxReceiptsPerFile is reached', async () => {
  // The engine loads its own copy of the plugin module, so the seam is driven on a ledger built here.
  const saved = limits.segmentBytesMax
  limits.segmentBytesMax = 2_000
  try {
    const s = readyLedger()
    const env = fakeEnv()
    for (let i = 0; i < 10; i++) commit(env.$, s, asReceipt(stepRec(i)))
    await s.chain

    expect(s.segments.length).toBeGreaterThan(1)
    expect(s.segments.length).toBeLessThan(10)
    const first = env.files.get(FILE)!
    expect(first.length).toBeGreaterThanOrEqual(2_000)
    // It rolled at the receipt that reached the limit: without its line it was under.
    const lastLine = first.slice(0, -1).split('\n').pop()!
    expect(first.length - lastLine.length - 1).toBeLessThan(2_000)
    expect(s.segments[0]!.bytes).toBe(first.length)
    const all = [...env.files.values()].flatMap(text => text.split('\n').filter(line => line !== '').map(line => JSON.parse(line).seq))
    expect(all.sort((a, b) => a - b)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
  } finally {
    limits.segmentBytesMax = saved
  }
})

test('rehydrate leaves an unreadable segment alone and skips a corrupt line, nothing throws', async ($, on) => {
  const unreadable = `${DEFAULT_DIR}/sess-1.1.jsonl`
  const files = {
    [FILE]:
      jsonl([stepRec(0)]) +
      'this is not json\n' +
      JSON.stringify({ schema_version: 'something.else', seq: 1 }) +
      '\n' +
      'null\n' +
      JSON.stringify(stepRec(7)) +
      '\n',
    [unreadable]: 'UNREADABLE-BODY',
  }
  const h = harness($, on, { files })
  h.world.unreadable.add(unreadable)
  await h.start()
  await h.step({ ...STEP, index: 1 })

  expect(h.world.files.get(unreadable)).toBe('UNREADABLE-BODY')
  expect(h.world.writes.every(write => write.path !== unreadable)).toBe(true)
  // Numbering continues after the highest good seq and after the unreadable segment.
  expect(h.lines(`${DEFAULT_DIR}/sess-1.2.jsonl`).map(r => r.seq)).toEqual([8])
  expect(await receiptsText(h)).toMatch(/step_observed 3/)
})

test('the command handlers answer `could not read the ledger.` when the table cannot be built', async ($, on) => {
  // A receipt file may hold anything that parses; a numeric model reaches the table code.
  const files = {
    [FILE]: jsonl([
      reqRec(0, { tool_use_id: 'toolu_odd', requested_model: 5, pinned: true, spawned_agent_id: 'agent-x' }),
      stepRec(1, { agent_id: 'agent-x', observed_model: 'claude-x' }),
    ]),
  }
  const h = harness($, on, { files })
  await h.start()
  expect((await h.run('route-ledger')).text).toBe('could not read the ledger.')
  expect((await h.run('route')).text).toBe('could not read the ledger.')
})
