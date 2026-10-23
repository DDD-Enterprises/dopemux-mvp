import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine, MockClock } from 'claude-code/testing'

import {
  familyOf,
  flushSegments,
  newLedger,
  parseConfig,
  summarize,
  toBindingFields,
} from './register.tsx'

const T0 = 1_792_000_000_000
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
    return root !== undefined && path.startsWith(`${root}/`) ? path.slice(root.length + 1) : path
  }
  const world = {
    clock,
    files: new Map<string, string>(Object.entries(opts.files ?? {})),
    dirs: new Set<string>(opts.dirs ?? ['.control-tower/state']),
    writes: [] as { path: string; text: string }[],
    failWrites: false,
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
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))
  on('session.id', () => ({ value: opts.sessionId ?? 'sess-1' }))
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
    if (world.failWrites) return { deny: 'disk full' }
    world.files.set(path, e.text)
    return { value: undefined }
  })
  on('fs.read', (_, e) => {
    const text = world.files.get(rel(e.path))
    return text === undefined ? { deny: `ENOENT ${e.path}` } : { value: text }
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
      await clock.advance(DEBOUNCE_MS)
    },
    async end(reason: 'clear' | 'other' = 'other') {
      await $.session.end({ reason, sessionId: 'sess-1', resume: { sessionId: 'sess-1' } as never })
      await clock.settle()
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

const DEBOUNCE_MS = 1_000
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
    description: 'Write the tests',
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

test('an unpinned Agent call toasts once, naming the type and description but not the prompt', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const { seen } = await h.agent({ subagent_type: 'Explore', description: 'Map the repo' })

  expect(seen).toHaveLength(1)
  expect(h.world.toasts).toHaveLength(1)
  expect(h.world.toasts[0]!.includes('Explore')).toBe(true)
  expect(h.world.toasts[0]!.includes('Map the repo')).toBe(true)
  expect(h.world.toasts[0]!.includes('SECRET-PROMPT')).toBe(false)

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

test('a long description is cut to 80 characters', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.agent({ model: 'haiku', description: 'x'.repeat(200) })
  expect(h.receipts()[0]!.description).toBe('x'.repeat(80))
})

test('next runs once with e unchanged when the write fails, and the next receipt heals the file', async ($, on) => {
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

test('session.end clear is not an end; any other reason stops recording', async ($, on) => {
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
  s.segments = [{ n: 0, path: 'd/x.jsonl', receipts: [{ seq: 0 } as never], bytes: 0, dirty: true }]
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

test('a child over its budget shows N/B ⚠ in the status', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.serverToolUses = [{ id: 'srv-1', name: 'advisor', input: {}, startedAt: 1, endedAt: 2 }]
  await stepAs(h, 'agent-7', 'claude-sonnet-5-5')
  await h.settleStatus()
  expect(h.status()).toBe('agents S×1 · advisor 1/0 ⚠')
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
  await h.settleStatus()
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
  expect(text).toMatch(new RegExp(FILE.replace(/[.]/g, '\\.')))
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
