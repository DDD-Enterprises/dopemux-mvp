import type { On, RenderElement } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine, MockClock, Plugin } from 'claude-code/testing'

const SEC = 1_000
const MIN = 60_000
const NOW0 = Date.UTC(2026, 9, 23, 12, 0, 0)

const ROOT = '/repo'
const OUT = '/repo/.dopemux/memory-bridge'
const PLUGIN = 'dopemux-memory-bridge'
const GIT = ['git', 'status', '--porcelain']
const MESSAGES = [{ role: 'user', text: 'hi', toolUses: [] }] as never

const LEDGER_TIMEOUT_MS = 15_000

function isGit(argv: readonly string[]): boolean {
  return argv.length === GIT.length && argv.every((part, i) => part === GIT[i])
}

// The exact replay argv of packet L01: nothing in it but the event JSON varies.
function isEmit(argv: readonly string[]): boolean {
  return (
    argv.length === 9 &&
    argv[0] === 'dopemux' &&
    argv[1] === 'capture' &&
    argv[2] === 'emit' &&
    argv[3] === '--event' &&
    argv[5] === '--mode' &&
    argv[6] === 'plugin' &&
    argv[7] === '--repo-root' &&
    argv[8] === ROOT
  )
}

const BAND = {
  plugin: PLUGIN,
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 10,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 10 },
    view: {},
  },
} as const

type WriteMode = 'ok' | 'fail' | 'slow'
type ProcMode = 'ok' | 'deny' | 'throw' | 'hang'
type LedgerMode = 'ok' | 'fail' | 'slow' // how `dopemux capture emit` answers

type Row = Record<string, unknown> & {
  id: string
  kind: string
  state: string
  goal: string
  files_touched: string[]
  decisions: string[]
  todos_completed: string[]
  note?: string
  intended_event: string | null
  session_id: string
  cwd_rel: string
  ts: string
  attempts: number
  v: number
}

type Options = {
  cwd?: string
  dopemux?: boolean // does <root>/.dopemux exist?
  files?: Record<string, string>
  gitOut?: string
  sid?: string
  store?: Record<string, unknown>
}

// Everything beneath the plugin is mocked: the clock, the store, the file
// system, the process, the session identity and the engine's own answers.
function harness($: Engine, on: On, opts: Options = {}) {
  const clock: MockClock = mock.clock(on, { now: NOW0 })
  const world = {
    clock,
    sid: opts.sid ?? 's1',
    cwd: opts.cwd ?? ROOT,
    files: new Map<string, string>(Object.entries(opts.files ?? {})),
    mtimes: new Map<string, number>(),
    dirs: new Set<string>([ROOT, `${ROOT}/.git`]),
    writeMode: 'ok' as WriteMode,
    procMode: 'ok' as ProcMode,
    gitOut: opts.gitOut ?? '',
    compactSkip: undefined as string | undefined,
    toolDeny: false,
    existsHangs: false,
    writes: [] as { path: string; text: string }[],
    active: 0,
    maxActive: 0,
    ledgerMode: 'ok' as LedgerMode,
    ledgerActive: 0,
    ledgerMaxActive: 0,
    procCalls: [] as { argv: readonly string[]; cwd: string | undefined; timeoutMs: number | undefined }[],
    emits: [] as {
      argv: readonly string[]
      event: Record<string, unknown>
      rowStateAtCall: string | undefined
    }[],
    registered: [] as { name: string; description: string; argumentHint: string | undefined }[],
    statuses: [] as (string | undefined)[],
    store: new Map<string, unknown>(Object.entries(opts.store ?? {})),
    storeSets: [] as string[],
    network: [] as string[],
    get status() {
      return world.statuses[world.statuses.length - 1]
    },
  }
  if (opts.dopemux !== false) world.dirs.add(`${ROOT}/.dopemux`)
  for (const path of world.files.keys()) world.mtimes.set(path, NOW0 - 48 * 60 * MIN)

  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))
  on('prompt.submit', (_, e) => ({ text: e.text }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('session.compact', (_, e) =>
    world.compactSkip === undefined ? { messages: e.messages } : { skip: world.compactSkip },
  )
  on('tool.call', () => (world.toolDeny ? { deny: 'not today' } : { result: {} }))
  on('session.id', () => ({ value: world.sid }))
  on('session.cwd', () => ({ value: world.cwd }))
  on('ui.status', (_, e) => {
    world.statuses.push(e.text)
    return { value: undefined }
  })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return h$(Text, 'engine band')
  })
  on('http.fetch', (_, e) => {
    world.network.push(e.url)
    throw new Error('the mod must not use the network')
  })

  on('store.get', (_, e) => ({ value: world.store.get(e.key) }))
  on('store.set', (_, e) => {
    world.storeSets.push(e.key)
    world.store.set(e.key, JSON.parse(JSON.stringify(e.value)))
    return { value: undefined }
  })
  on('store.delete', (_, e) => {
    world.store.delete(e.key)
    return { value: undefined }
  })
  on('store.keys', () => ({ value: [...world.store.keys()] }))

  on('fs.exists', async (_, e) => {
    if (world.existsHangs) await clock.sleep(1000 * MIN)
    return { value: world.dirs.has(e.path) || world.files.has(e.path) }
  })
  on('fs.read', (_, e) => {
    const text = world.files.get(e.path)
    return text === undefined ? { deny: 'ENOENT' } : { value: text }
  })
  on('fs.list', (_, e) => {
    const prefix = e.path.replace(/\/+$/, '') + '/'
    const entries = [...world.files.entries()]
      .filter(([path]) => path.startsWith(prefix) && !path.slice(prefix.length).includes('/'))
      .map(([path, text]) => ({
        name: path.slice(prefix.length),
        kind: 'file' as const,
        size: text.length,
        mtimeMs: world.mtimes.get(path) ?? 0,
        isLink: false,
      }))
    return world.dirs.has(e.path.replace(/\/+$/, '')) || entries.length > 0
      ? { value: entries }
      : { deny: 'ENOENT' }
  })
  on('fs.write', async (_, e) => {
    world.writes.push({ path: e.path, text: e.text })
    if (world.writeMode === 'fail') return { deny: 'EACCES' }
    world.active += 1
    world.maxActive = Math.max(world.maxActive, world.active)
    try {
      if (world.writeMode === 'slow') await clock.sleep(10 * MIN)
      world.files.set(e.path, e.text)
      world.mtimes.set(e.path, clock.now())
      const dir = e.path.slice(0, e.path.lastIndexOf('/'))
      world.dirs.add(dir)
      return { value: undefined }
    } finally {
      world.active -= 1
    }
  })
  on('command.register', (_, e) => {
    world.registered.push({ name: e.name, description: e.description, argumentHint: e.argumentHint })
    return { value: { command: e.name } }
  })
  on('process.run', async (_, e) => {
    world.procCalls.push({ argv: e.argv, cwd: e.init?.cwd, timeoutMs: e.init?.timeoutMs })
    if (world.procMode === 'hang') await clock.sleep(1000 * MIN)
    if (world.procMode === 'deny') return { deny: 'process is not available here' }
    if (world.procMode === 'throw') throw new Error('process.run blew up')
    if (e.argv[0] === 'dopemux') {
      const raw = e.argv[e.argv.indexOf('--event') + 1] ?? '{}'
      const event = JSON.parse(raw) as Record<string, unknown>
      const row = readOutbox(world.files, String(event.session_id))?.rows.find(r => r.id === event.event_id)
      world.emits.push({ argv: e.argv, event, rowStateAtCall: row?.state })
      world.ledgerActive += 1
      world.ledgerMaxActive = Math.max(world.ledgerMaxActive, world.ledgerActive)
      try {
        if (world.ledgerMode === 'slow') await clock.sleep(10 * MIN)
        const exitCode = world.ledgerMode === 'fail' ? 1 : 0
        return {
          value: {
            exitCode,
            stdout: '',
            stderr: exitCode === 0 ? '' : 'capture failed',
            isStdoutTruncated: false,
            isStderrTruncated: false,
          },
        }
      } finally {
        world.ledgerActive -= 1
      }
    }
    return {
      value: {
        exitCode: 0,
        stdout: world.gitOut,
        stderr: '',
        isStdoutTruncated: false,
        isStderrTruncated: false,
      },
    }
  })

  let turnCount = 0
  const api = {
    world,
    async start(cwd = world.cwd) {
      world.cwd = cwd
      await $.session.start({ cwd, surface: 'terminal', isInteractive: true })
      await clock.settle()
    },
    async end(reason: 'clear' | 'resume' | 'logout' | 'prompt_input_exit' | 'other' = 'other') {
      await $.session.end({
        reason,
        sessionId: world.sid,
        resume: { sessionId: world.sid } as never,
      })
      await clock.settle()
    },
    async prompt(text = 'hello') {
      await $.prompt.submit({
        text,
        wait: false,
        origin: { kind: 'composer' },
      })
      await clock.settle()
    },
    async tool(input: Record<string, unknown>, agentId?: string) {
      await $.tool.call({
        tool_use_id: `tu${Math.random()}`,
        ...(agentId === undefined ? {} : { agentId }),
        ...input,
      } as never)
      await clock.settle()
    },
    async edit(file: string, agentId?: string) {
      await api.tool({ tool: 'Edit', file_path: file, old_string: 'a', new_string: 'b' }, agentId)
    },
    async todos(list: [string, 'pending' | 'in_progress' | 'completed'][], agentId?: string) {
      await api.tool(
        {
          tool: 'TodoWrite',
          todos: list.map(([content, status]) => ({ content, status, activeForm: content })),
        },
        agentId,
      )
    },
    // One whole main-loop turn: prompt, start, whatever `during` does, complete.
    async turn(
      text: string,
      answer = 'done',
      during?: () => Promise<void>,
      turnId = `t${(turnCount += 1)}`,
    ) {
      await api.prompt(text)
      await $.turn.start({ text, turnId })
      await clock.settle()
      if (during !== undefined) await during()
      await $.turn.complete({
        answer,
        durationMs: 1,
        isAborted: false,
        turnId,
        reason: 'answer',
      })
      await clock.settle()
      return turnId
    },
    rows(sid = world.sid) {
      return readOutbox(world.files, sid)?.rows ?? []
    },
    gen(sid = world.sid) {
      return readOutbox(world.files, sid)?.gen
    },
    async run(command: string, args = '') {
      const answer = await $.command.run({
        command,
        args,
        origin: { kind: 'composer' },
        presentation: { isFullscreen: false, columns: 80 },
      })
      await clock.settle()
      return answer
    },
    async band(surface: 'terminal' | 'desktop' = 'terminal') {
      const ui = await $.ui.mount({ ...BAND, surface })
      const found = await ui.find({ type: 'Text', text: /Welcome back/ })
      const engine = await ui.find({ type: 'Text', text: /engine band/ })
      await ui.unmount()
      return { text: found?.text, hasEngine: engine !== undefined }
    },
  }
  return api
}

// --- the outbox file format, as the module writes it -----------------------------

function primary(sid: string): string {
  return `${OUT}/outbox-${sid}.jsonl`
}
function alternate(sid: string): string {
  return `${OUT}/outbox-${sid}.alt.jsonl`
}

function genText(sid: string, gen: number, rows: object[], dropped = 0): string {
  const lines = [
    JSON.stringify({ v: 1, meta: 'gen', gen, session_id: sid, dropped }),
    ...rows.map(r => JSON.stringify(r)),
    JSON.stringify({ v: 1, meta: 'eof', gen, rows: rows.length }),
  ]
  return lines.join('\n') + '\n'
}

function parseGen(text: string | undefined): { gen: number; dropped: number; rows: Row[] } | undefined {
  if (text === undefined) return undefined
  const lines = text.split('\n').filter(l => l.trim() !== '')
  if (lines.length < 2) return undefined
  try {
    const head = JSON.parse(lines[0]!)
    const foot = JSON.parse(lines[lines.length - 1]!)
    if (head.meta !== 'gen' || foot.meta !== 'eof') return undefined
    if (head.gen !== foot.gen || foot.rows !== lines.length - 2) return undefined
    const rows = lines.slice(1, -1).map(l => JSON.parse(l) as Row)
    return { gen: head.gen as number, dropped: head.dropped as number, rows }
  } catch {
    return undefined
  }
}

function readOutbox(files: Map<string, string>, sid: string) {
  const a = parseGen(files.get(primary(sid)))
  const b = parseGen(files.get(alternate(sid)))
  if (a === undefined) return b
  if (b === undefined) return a
  return a.gen >= b.gen ? a : b
}

function seedRow(id: string, state: 'pending' | 'sent' | 'dead', over: Record<string, unknown> = {}) {
  return {
    v: 1,
    id,
    ts: new Date(NOW0 - 48 * 60 * MIN).toISOString(),
    kind: 'turn',
    session_id: 'old',
    cwd_rel: '.',
    goal: 'an older goal',
    files_touched: [],
    decisions: [],
    todos_completed: [],
    intended_event: null,
    state,
    attempts: 0,
    ...over,
  }
}

// A row the ledger replay is waiting to deliver (the only kind the status line counts).
const WAITING = { kind: 'task', intended_event: 'task.completed', todos_completed: ['waiting'] }

function startedOutbox(sid: string, rows: object[], gen = 1, dropped = 0) {
  return { [primary(sid)]: genText(sid, gen, rows, dropped) }
}

// `h` (the JSX factory) is a global the engine provides; a .ts test calls it
// directly. Named h$ so it does not collide with the harness variable `h`.
function h$(tag: Parameters<typeof h>[0], ...children: unknown[]) {
  return h(tag, null, ...children) as RenderElement
}

// A second plugin that draws its own AbovePrompt Box and never calls next,
// as the Pulse focus band does. `register` closes over nothing of this file.
function pulseLike(tier: 'prepend' | 'append'): Plugin {
  return {
    name: 'pulse-like',
    tier,
    register(on) {
      on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
        const { Box, Text } = $.ui.resolve(e)
        return h(Box, null, h(Text, null, 'pulse band')) as RenderElement
      })
    },
  }
}

// ---------------------------------------------------------------------------------
// capture

test('a turn records the goal, files, a marked decision and completed todos', async ($, on) => {
  const h = harness($, on, { cwd: '/repo/pkg' })
  await h.start()

  await h.turn('Fix the parser bug in pkg/a.py', 'All fixed.\nDecision: keep the old parser API\nbye', async () => {
    await h.edit('/repo/pkg/a.py')
    await h.edit('/repo/pkg/a.py')
    await h.tool({ tool: 'Write', file_path: '/repo/pkg/b.py', content: 'x' })
    await h.tool({ tool: 'NotebookEdit', notebook_path: '/repo/pkg/n.ipynb', new_source: 'x' })
    await h.edit('/elsewhere/outside.py')
    await h.todos([['Write tests', 'in_progress'], ['Fix parser', 'pending']])
    await h.todos([['Write tests', 'completed'], ['Fix parser', 'in_progress']])
  })

  const turn = h.rows().find(r => r.kind === 'turn')!
  expect(turn.v).toBe(1)
  expect(turn.session_id).toBe('s1')
  expect(turn.cwd_rel).toBe('pkg')
  expect(turn.goal).toBe('Fix the parser bug in pkg/a.py')
  expect(turn.files_touched).toEqual(['pkg/a.py', 'pkg/b.py', 'pkg/n.ipynb'])
  expect(turn.decisions).toEqual(['keep the old parser API'])
  expect(turn.todos_completed).toEqual(['Write tests'])
  expect(turn.intended_event).toBe(null)
  expect(turn.state).toBe('pending')
  expect(turn.attempts).toBe(0)
  expect(turn.id).toMatch(/^[0-9a-f]{24}$/)

  const task = h.rows().find(r => r.kind === 'task')!
  expect(task.intended_event).toBe('task.completed')
  expect(task.todos_completed).toEqual(['Write tests'])
  // Only the task row waits for the ledger; the turn row is local history.
  expect(h.world.status).toBe('📮 1 pending')
})

test('no raw prompt, tool output or answer text reaches the outbox', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const longPrompt = 'Please refactor everything. ' + 'private-body '.repeat(100)
  await h.turn(longPrompt, 'The assistant long answer: ' + 'secret-answer-body '.repeat(50) + '\nDecision: ship it')
  const text = h.world.files.get(primary('s1'))!
  expect(text).not.toContain('secret-answer-body')
  expect(text).not.toContain('private-body private-body private-body private-body private-body private-body private-body private-body private-body private-body private-body private-body')
  expect(h.rows()[0]!.goal.length).toBeLessThanOrEqual(160)
  expect(h.rows()[0]!.decisions).toEqual(['ship it'])
})

test('decision capture is marker-only: bold forms, three at most, 200 characters each', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const answer = [
    'Notes: we decided things.',
    'a decision: lowercase is not a marker',
    '**Decision:** first bolded',
    '**DECISION**: second bolded',
    'DECISION: third ' + 'x'.repeat(300),
    'Decision: fourth is dropped',
  ].join('\n')
  await h.turn('go', answer)
  const decisions = h.rows()[0]!.decisions
  expect(decisions).toHaveLength(3)
  expect(decisions[0]).toBe('first bolded')
  expect(decisions[1]).toBe('second bolded')
  expect(decisions[2]!.length).toBe(200)

  const none = await (async () => {
    await h.turn('again', 'we made a decision to wait')
    return h.rows().filter(r => r.kind === 'turn').pop()!
  })()
  expect(none.decisions).toEqual([])
})

test('decision.logged is never emitted anywhere', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('go', 'Decision: x')
  const all = JSON.stringify([...h.world.files.values()]) + JSON.stringify([...h.world.store.values()])
  expect(all).not.toContain('decision.logged')
  expect(h.rows().every(r => r.intended_event === null || r.intended_event === 'task.completed' || r.intended_event === 'manual.memory_store')).toBe(true)
})

test('a TodoWrite completion adds one task record per item, once', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('work', 'ok', async () => {
    await h.todos([['A', 'in_progress'], ['B', 'pending']])
    await h.todos([['A', 'completed'], ['B', 'in_progress']])
    // The same list again completes nothing new.
    await h.todos([['A', 'completed'], ['B', 'in_progress']])
    await h.todos([['A', 'completed'], ['B', 'completed']])
  })
  const tasks = h.rows().filter(r => r.kind === 'task')
  expect(tasks.map(t => t.todos_completed[0])).toEqual(['A', 'B'])
  expect(h.rows().find(r => r.kind === 'turn')!.todos_completed).toEqual(['A', 'B'])
})

test('subagent loops are ignored: turns, todos and the goal', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.prompt('main goal')
  await $.turn.start({ text: 'main goal', turnId: 'main1' })
  await $.turn.start({ text: 'SUBAGENT PROMPT', turnId: 'sub1', agentId: 'agent-1' })
  await h.todos([['Sub task', 'completed']], 'agent-1')
  await $.turn.complete({
    answer: 'Decision: subagent decision',
    durationMs: 1,
    isAborted: false,
    turnId: 'sub1',
    agentId: 'agent-1',
    reason: 'answer',
  })
  await h.world.clock.settle()
  expect(h.rows()).toEqual([])

  await $.turn.complete({ answer: 'fin', durationMs: 1, isAborted: false, turnId: 'main1', reason: 'answer' })
  await h.world.clock.settle()
  const rows = h.rows()
  expect(rows).toHaveLength(1)
  expect(rows[0]!.goal).toBe('main goal')
  expect(rows[0]!.todos_completed).toEqual([])
  expect(rows[0]!.decisions).toEqual([])
})

test('the per-turn state resets between turns', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('one', 'a', async () => {
    await h.edit('/repo/one.py')
    await h.todos([['T', 'completed']])
  })
  await h.turn('two', 'b', async () => {
    await h.edit('/repo/two.py')
  })
  const turns = h.rows().filter(r => r.kind === 'turn')
  expect(turns[0]!.files_touched).toEqual(['one.py'])
  expect(turns[0]!.todos_completed).toEqual(['T'])
  expect(turns[1]!.files_touched).toEqual(['two.py'])
  expect(turns[1]!.todos_completed).toEqual([])
})

test('files are capped at 30 and todo titles at 10 per turn', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('big', 'ok', async () => {
    for (let i = 0; i < 40; i += 1) await h.edit(`/repo/f${i}.py`)
    await h.todos(Array.from({ length: 15 }, (_, i) => [`todo ${i}`, 'pending'] as [string, 'pending']))
    await h.todos(Array.from({ length: 15 }, (_, i) => [`todo ${i}`, 'completed'] as [string, 'completed']))
  })
  const turn = h.rows().find(r => r.kind === 'turn')!
  expect(turn.files_touched).toHaveLength(30)
  expect(turn.todos_completed).toHaveLength(10)
})

test('compact appends a record and passes the result through unchanged', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('before compaction', 'ok')
  const messages = MESSAGES
  const answered = await $.session.compact({ trigger: 'auto', messages })
  await h.world.clock.settle()
  expect(answered).toEqual({ messages })
  const compact = h.rows().filter(r => r.kind === 'compact')
  expect(compact).toHaveLength(1)
  expect(compact[0]!.goal).toBe('before compaction')

  // A subagent's own compaction is not ours.
  await $.session.compact({ trigger: 'auto', agentId: 'agent-1', messages })
  await h.world.clock.settle()
  expect(h.rows().filter(r => r.kind === 'compact')).toHaveLength(1)
})

test('a skipped compaction records nothing and is passed through', async ($, on) => {
  const h = harness($, on)
  h.world.compactSkip = 'no thanks'
  await h.start()
  await h.turn('x', 'ok')
  const answered = await $.session.compact({ trigger: 'manual', messages: MESSAGES })
  await h.world.clock.settle()
  expect(answered).toEqual({ skip: 'no thanks' })
  expect(h.rows().filter(r => r.kind === 'compact')).toEqual([])
})

test('observing hooks pass the result through untouched', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.prompt('hi')
  const started = await $.turn.start({ text: 'hi', turnId: 'tx' })
  expect(started).toEqual({ turnId: 'tx' })
  const result = await $.tool.call({
    tool: 'Edit',
    tool_use_id: 'tu1',
    file_path: '/repo/a.py',
    old_string: 'a',
    new_string: 'b',
  } as never)
  expect(result).toEqual({ result: {} })
  const done = await $.turn.complete({
    answer: 'the answer',
    durationMs: 5,
    isAborted: false,
    turnId: 'tx',
    reason: 'answer',
  })
  expect(done).toEqual({ text: 'the answer' })
})


test('a refused tool call touched nothing', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('refused', 'ok', async () => {
    h.world.toolDeny = true
    await h.edit('/repo/denied.py')
    await h.todos([['Never done', 'completed']])
    h.world.toolDeny = false
  })
  const turn = h.rows().find(r => r.kind === 'turn')!
  expect(turn.files_touched).toEqual([])
  expect(turn.todos_completed).toEqual([])
})

test('a turn with nothing to say records nothing', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 'bare', reason: 'answer' })
  await h.world.clock.settle()
  expect(h.rows()).toEqual([])
  expect(h.world.writes).toEqual([])
})

test('an aborted turn is still recorded', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.prompt('interrupt me')
  await $.turn.start({ text: 'interrupt me', turnId: 'ab1' })
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: true, turnId: 'ab1', reason: 'aborted' })
  await h.world.clock.settle()
  expect(h.rows()[0]!.goal).toBe('interrupt me')
})

test('a continuation turn with no text keeps the last goal', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('The real goal', 'ok')
  await h.turn('', 'continued', undefined, 'cont1')
  const turns = h.rows().filter(r => r.kind === 'turn')
  expect(turns[1]!.goal).toBe('The real goal')
})

// ---------------------------------------------------------------------------------
// redactor

// One secret per turn, each in the goal, a decision and a todo title, so the
// length caps cannot hide a leak. The first four are the shapes the repo's own
// redactor (W01 Q11) leaves unmasked.
const LEAKY: readonly (readonly [string, string])[] = [
  ['sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_abcdef', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'],
  ['https://alice:hunter2@example.com/path', 'hunter2'],
  ['alice.smith@example.org', 'alice.smith@example.org'],
  ['DATABASE_URL=postgresql://user:pw123@db.internal:5432/app', 'pw123'],
  ['sk-proj1234567890abcdefghijklmnop', 'sk-proj1234567890abcdefghijklmnop'],
  ['ghp_abcdefghijklmnopqrstuvwxyz0123456789', 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'],
  ['AKIAIOSFODNN7EXAMPLE', 'AKIAIOSFODNN7EXAMPLE'],
  ['Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456', 'abcdefghijklmnopqrstuvwxyz123456'],
  ['password=hunter22', 'hunter22'],
  ['token=abcdef123456', 'abcdef123456'],
  ['secret=shhhhhhh', 'shhhhhhh'],
  ['-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA1234\n-----END RSA PRIVATE KEY-----', 'MIIEowIBAAKCAQEA1234'],
  ['-----BEGIN PRIVATE KEY-----\nMIIBVQIBADANBgkqhkiG9w0B', 'MIIBVQIBADANBgkqhkiG9w0B'],
  ['{"api_key": "zzzz-json-secret-zzzz"}', 'zzzz-json-secret-zzzz'],
]

for (const [secret, needle] of LEAKY) {
  test(`the redactor masks ${secret.slice(0, 18).replace(/\n/g, ' ')}`, async ($, on) => {
    const h = harness($, on)
    await h.start()
    await h.turn(`use ${secret} here`, `Decision: rotate ${secret} soon`, async () => {
      await h.todos([[`Rotate ${secret}`, 'completed']])
    })
    const stored = [...h.world.files.values()].join('\n')
    expect(stored).not.toContain(needle)
    expect(stored).toContain('REDACTED')
    // Each place a string is kept was masked, not just the goal.
    const turn = h.rows().find(r => r.kind === 'turn')!
    expect(turn.decisions[0]).toContain('REDACTED')
    expect(turn.todos_completed[0]).toContain('REDACTED')
  })
}

test('the redactor leaves ordinary text and short words alone', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Explain the task-runner and the sk-learn tokenizer; fix src/auth/token.ts line 5', 'ok')
  expect(h.rows()[0]!.goal).toBe('Explain the task-runner and the sk-learn tokenizer; fix src/auth/token.ts line 5')
})

test('home-directory paths are normalised', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('look at /Users/alice/code/app/main.py and /home/bob/x.txt', 'ok')
  const goal = h.rows()[0]!.goal
  expect(goal).not.toContain('alice')
  expect(goal).not.toContain('bob')
  expect(goal).toContain('~/code/app/main.py')
})

// ---------------------------------------------------------------------------------
// ids

test('ids are deterministic per session, turn and kind and re-appends are ignored', async ($, on) => {
  const first = harness($, on)
  await first.start()
  await first.turn('same', 'ok', undefined, 'turn-fixed')
  const id = first.rows()[0]!.id

  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 'turn-fixed', reason: 'answer' })
  await first.world.clock.settle()
  expect(first.rows().filter(r => r.kind === 'turn')).toHaveLength(1)

  expect(id).toMatch(/^[0-9a-f]{24}$/)
  // A different turn id gives a different id.
  await first.turn('same', 'ok', undefined, 'turn-other')
  const ids = new Set(first.rows().map(r => r.id))
  expect(ids.size).toBe(first.rows().length)
})

// The id is the first 24 hex digits of sha256(session_id NUL turn_id NUL kind),
// computed here independently of the module.
test('the id is the truncated sha256 of session, turn and kind', async ($, on) => {
  const h = harness($, on, { sid: 'sess-9' })
  await h.start()
  await h.turn('same', 'ok', undefined, 'turn-fixed')
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('sess-9\u0000turn-fixed\u0000turn'))
  const hex = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('')
  expect(h.rows('sess-9')[0]!.id).toBe(hex.slice(0, 24))
})

// ---------------------------------------------------------------------------------
// ring cap

test('the file is a rewrite-in-place ring: two alternating generations', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('one', 'a')
  const first = h.gen()
  await h.turn('two', 'b')
  const second = h.gen()
  expect(second!).toBeGreaterThan(first!)
  expect(h.world.files.has(primary('s1'))).toBe(true)
  expect(h.world.files.has(alternate('s1'))).toBe(true)
  // The newest generation holds both turns.
  expect(h.rows().filter(r => r.kind === 'turn')).toHaveLength(2)
  // Every file is a complete, valid generation.
  expect(parseGen(h.world.files.get(primary('s1')))).toBeDefined()
  expect(parseGen(h.world.files.get(alternate('s1')))).toBeDefined()
})

test('every row is at most 8 KB', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('x'.repeat(5000), 'Decision: ' + 'y'.repeat(5000), async () => {
    for (let i = 0; i < 40; i += 1) await h.edit(`/repo/${'d'.repeat(200)}/file${i}.py`)
    await h.todos(Array.from({ length: 12 }, (_, i) => [`${'t'.repeat(500)}${i}`, 'completed'] as [string, 'completed']))
  })
  const text = h.world.files.get(primary('s1'))!
  for (const line of text.split('\n').filter(Boolean)) {
    expect(new TextEncoder().encode(line).length).toBeLessThanOrEqual(8192)
  }
  expect(h.rows().find(r => r.kind === 'turn')).toBeDefined()
})

test('over the 1 MiB cap the oldest sent rows go first and drops are counted', async ($, on) => {
  const body = 'x'.repeat(6000)
  const sent = Array.from({ length: 100 }, (_, i) => seedRow(`sent${i}`, 'sent', { goal: body }))
  const pending = Array.from({ length: 70 }, (_, i) => seedRow(`pend${i}`, 'pending', { ...WAITING, goal: body }))
  const h = harness($, on, { files: startedOutbox('s1', [...sent, ...pending]) })
  await h.start()
  await h.turn('new work', 'ok')
  const rows = h.rows()
  for (const text of [h.world.files.get(alternate('s1'))!]) {
    expect(new TextEncoder().encode(text).length).toBeLessThanOrEqual(1_048_576)
  }
  expect(h.gen()).toBe(2)
  // No pending row was dropped while sent rows could be.
  expect(rows.filter(r => r.state === 'pending').length).toBe(71)
  expect(rows.some(r => r.id === 'sent0')).toBe(false)
  expect(rows.some(r => r.id === 'sent99')).toBe(true)
  expect(h.world.status).toMatch(/^📮 70 pending \+\d+ dropped$/)
})

test('with no sent rows left the oldest pending rows are dropped, and counted', async ($, on) => {
  const body = 'x'.repeat(6000)
  const pending = Array.from({ length: 175 }, (_, i) => seedRow(`pend${i}`, 'pending', { goal: body }))
  const h = harness($, on, { files: startedOutbox('s1', pending) })
  await h.start()
  await h.turn('new work', 'ok')
  const rows = h.rows()
  expect(rows.some(r => r.id === 'pend0')).toBe(false)
  expect(rows.some(r => r.id === 'pend174')).toBe(true)
  const dropped = Number(/\+(\d+) dropped/.exec(h.world.status ?? '')?.[1])
  expect(dropped).toBeGreaterThan(0)
  expect(rows.length + dropped).toBe(176)
})

// ---------------------------------------------------------------------------------
// generation recovery

test('a torn newer generation is skipped and the older valid one is used', async ($, on) => {
  const older = [seedRow('keep1', 'pending', WAITING), seedRow('keep2', 'pending', WAITING)]
  const tornFull = genText('s1', 6, [...older, seedRow('lost', 'pending', WAITING)])
  const files = {
    [primary('s1')]: genText('s1', 5, older),
    [alternate('s1')]: tornFull.slice(0, tornFull.length - 60),
  }
  const h = harness($, on, { files })
  await h.start()
  expect(h.world.status).toBe('📮 2 pending')

  await h.turn('after recovery', 'ok')
  // The next write goes to the file that held the torn copy, as generation 6.
  const last = h.world.writes[h.world.writes.length - 1]!
  expect(last.path).toBe(alternate('s1'))
  expect(h.gen()).toBe(6)
  expect(h.rows().map(r => r.id)).toContain('keep1')
  expect(h.rows().map(r => r.id)).not.toContain('lost')
})

test('the highest valid generation wins when both are whole', async ($, on) => {
  const files = {
    [primary('s1')]: genText('s1', 3, [seedRow('g3', 'pending', WAITING)]),
    [alternate('s1')]: genText('s1', 4, [seedRow('g3', 'pending', WAITING), seedRow('g4', 'pending', WAITING)]),
  }
  const h = harness($, on, { files })
  await h.start()
  expect(h.world.status).toBe('📮 2 pending')
})

test('garbage lines inside a whole generation are skipped, not fatal', async ($, on) => {
  const text = genText('s1', 2, [seedRow('ok1', 'pending', WAITING)]).split('\n')
  text.splice(1, 0, '{not json')
  const bad = text.join('\n').replace(/"rows":1/, '"rows":2')
  const h = harness($, on, { files: { [primary('s1')]: bad } })
  await h.start()
  expect(h.world.status).toBe('📮 1 pending')
})

// ---------------------------------------------------------------------------------
// status line

test('status line: clear, pending count, memory-only, write failed, dropped suffix', async ($, on) => {
  const h = harness($, on)
  await h.start()
  expect(h.world.status).toBe('📮 clear')

  // A turn row is local history: it never waits for the ledger.
  await h.turn('one', 'ok')
  expect(h.world.status).toBe('📮 clear')
  await h.turn('two', 'ok')
  expect(h.world.status).toBe('📮 clear')

  await h.todos([['T1', 'completed']])
  expect(h.world.status).toBe('📮 1 pending')
  await h.todos([['T1', 'completed'], ['T2', 'completed']])
  expect(h.world.status).toBe('📮 2 pending')
})

test('status line counts replayable pending rows already on disk at session start', async ($, on) => {
  const other = [
    seedRow('o1', 'pending', WAITING),
    seedRow('o2', 'sent', WAITING),
    seedRow('o3', 'pending', WAITING),
    seedRow('o4', 'pending'), // a prior turn row: local history, not counted
    seedRow('o5', 'pending', { kind: 'compact' }),
    seedRow('o6', 'pending', { kind: 'end' }),
  ]
  const h = harness($, on, { files: startedOutbox('older', other) })
  await h.start()
  expect(h.world.status).toBe('📮 2 pending')
  await h.turn('one', 'ok')
  expect(h.world.status).toBe('📮 2 pending')
})

test('prior-session turn rows alone leave the status line clear', async ($, on) => {
  const other = [seedRow('t1', 'pending'), seedRow('t2', 'pending', { kind: 'compact' })]
  const h = harness($, on, { files: startedOutbox('older', other) })
  await h.start()
  expect(h.world.status).toBe('📮 clear')
})

test('status goes clear -> 1 pending after a completed todo -> clear once it is sent', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('talk only', 'ok')
  expect(h.world.status).toBe('📮 clear')
  await finishTasks(h, ['Do it'])
  expect(h.world.status).toBe('📮 1 pending')
  await h.world.clock.advance(61 * SEC)
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('sent')
  expect(h.world.status).toBe('📮 clear')
  // The turn rows are still there, still 'pending' in the file.
  expect(h.rows().filter(r => r.kind === 'turn').every(r => r.state === 'pending')).toBe(true)
})

test('without <root>/.dopemux the outbox stays in memory plus the store and says so', async ($, on) => {
  const h = harness($, on, { dopemux: false })
  await h.start()
  expect(h.world.status).toBe('📮 memory-only')
  await h.turn('one', 'ok')
  expect(h.world.status).toBe('📮 memory-only')
  expect(h.world.writes).toEqual([])
  expect(h.world.dirs.has(`${ROOT}/.dopemux`)).toBe(false)
  expect(h.world.storeSets.some(k => k.startsWith('outbox'))).toBe(true)
})

test('no .git or .dopemux anywhere above the cwd means memory-only too', async ($, on) => {
  const h = harness($, on)
  h.world.dirs.clear()
  await h.start('/nowhere/deep')
  await h.turn('one', 'ok')
  expect(h.world.writes).toEqual([])
  expect(h.world.status).toBe('📮 memory-only')
})

test('the root is the nearest .git/.dopemux ancestor, not the session repo root', async ($, on) => {
  const h = harness($, on, { cwd: '/repo/sub/deeper' })
  h.world.dirs.add('/repo/sub')
  h.world.dirs.add('/repo/sub/.dopemux')
  await h.start()
  await h.turn('x', 'ok')
  expect(h.world.writes[0]!.path.startsWith('/repo/sub/.dopemux/memory-bridge/outbox-s1')).toBe(true)
})

test('a write failure never surfaces and the status line shows it, then recovers', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.writeMode = 'fail'
  await h.turn('one', 'ok') // must resolve normally
  expect(h.world.status).toBe('⚠ outbox write failed')

  h.world.writeMode = 'ok'
  await h.turn('two', 'ok')
  expect(h.world.status).toBe('📮 clear')
  expect(h.rows().filter(r => r.kind === 'turn')).toHaveLength(2)
})

test('after a failed write the retry reuses the same target and spares the intact copy', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('one', 'ok') // generation 1, primary
  h.world.writeMode = 'fail'
  await h.turn('two', 'ok') // generation 2 attempted, alternate, refused
  h.world.writeMode = 'ok'
  await h.turn('three', 'ok') // generation 2 again, alternate
  expect(h.world.writes.map(w => w.path)).toEqual([primary('s1'), alternate('s1'), alternate('s1')])
  expect(h.gen()).toBe(2)
  // The first copy was never rewritten while the second was failing.
  expect(parseGen(h.world.files.get(primary('s1')))!.rows.filter(r => r.kind === 'turn')).toHaveLength(1)
  expect(h.rows().filter(r => r.kind === 'turn')).toHaveLength(3)
})

test('a hung write is raced, flagged, and never piles up overlapping writes', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.writeMode = 'slow'
  for (let i = 0; i < 5; i += 1) await h.turn(`turn ${i}`, 'ok')
  await h.world.clock.advance(4 * SEC)
  expect(h.world.status).toBe('⚠ outbox write failed')
  expect(h.world.maxActive).toBe(1)
  expect(h.world.writes).toHaveLength(1)

  // The hung call finally returns; what accumulated goes out as one write.
  h.world.writeMode = 'ok'
  await h.world.clock.advance(11 * MIN)
  expect(h.world.maxActive).toBe(1)
  expect(h.world.writes).toHaveLength(2)
  expect(h.world.status).toBe('📮 clear')
  expect(h.rows().filter(r => r.kind === 'turn')).toHaveLength(5)
})


test('a hung file system cannot wedge the session start', async ($, on) => {
  const h = harness($, on)
  h.world.existsHangs = true
  let isStarted = false
  const started = $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true }).then(() => {
    isStarted = true
  })
  await h.world.clock.advance(2 * SEC)
  await started
  expect(isStarted).toBe(true)
})

test('memory-only rows are kept in the store', async ($, on) => {
  const h = harness($, on, { dopemux: false })
  await h.start()
  await h.turn('kept in the store', 'Decision: store it')
  const saved = h.world.store.get('outbox:s1') as { rows: Row[] }
  expect(saved.rows[0]!.goal).toBe('kept in the store')
  expect(saved.rows[0]!.decisions).toEqual(['store it'])
})

test('a later run of the same session id finds its stored rows again', async ($, on) => {
  const earlier = { v: 1, gen: 3, dropped: 0, rows: [seedRow('st1', 'pending', { goal: 'kept in the store' })] }
  const h = harness($, on, { dopemux: false, store: { 'outbox:s1': earlier } })
  await h.start()
  expect(h.world.status).toBe('📮 memory-only')
  await h.turn('second', 'ok')
  const next = h.world.store.get('outbox:s1') as { rows: Row[] }
  expect(next.rows.map(r => r.goal)).toEqual(['kept in the store', 'second'])
})

test('old stored sessions are pruned to the newest three', async ($, on) => {
  const old = (n: number) => [`outbox:old${n}`, { v: 1, gen: 1, dropped: 0, rows: [] }] as const
  const h = harness($, on, { dopemux: false, store: Object.fromEntries([old(1), old(2), old(3), old(4)]) })
  await h.start()
  await h.turn('now', 'ok')
  const keys = [...h.world.store.keys()].filter(k => k.startsWith('outbox:'))
  expect(keys).toHaveLength(3)
  expect(keys).toContain('outbox:s1')
})

// ---------------------------------------------------------------------------------
// session end

test('session.end appends a final record and cancels everything on a real end', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('last', 'ok')
  await h.end('other')
  expect(h.rows().some(r => r.kind === 'end')).toBe(true)
  expect(h.world.status).toBeUndefined()

  // Nothing wakes up after the end: no draw-triggering timers run.
  const writes = h.world.writes.length
  const calls = h.world.procCalls.length
  await h.world.clock.advance(300 * MIN)
  expect(h.world.writes).toHaveLength(writes)
  expect(h.world.procCalls).toHaveLength(calls)
})

for (const reason of ['resume', 'logout', 'prompt_input_exit'] as const) {
  test(`session.end (${reason}) is a real end`, async ($, on) => {
    const h = harness($, on)
    await h.start()
    await h.turn('x', 'ok')
    await h.end(reason)
    expect(h.rows().some(r => r.kind === 'end')).toBe(true)
    expect(h.world.status).toBeUndefined()
  })
}

test('session.end with reason clear appends but keeps running on the new session id', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('before clear', 'ok')

  h.world.sid = 's2' // /clear: a fresh session id, no session.start
  // (the end event carries the id of the session that ends)
  await $.session.end({ reason: 'clear', sessionId: 's1', resume: { sessionId: 's1' } as never })
  await h.world.clock.settle()

  expect(h.rows('s1').some(r => r.kind === 'end')).toBe(true)
  expect(h.world.status).toBeDefined()

  await h.turn('after clear', 'ok')
  expect(h.rows('s2').filter(r => r.kind === 'turn')).toHaveLength(1)
  expect(h.rows('s2')[0]!.goal).toBe('after clear')
  // The first session's file is closed and untouched by the new turn.
  expect(h.rows('s1').filter(r => r.kind === 'turn')).toHaveLength(1)

  // A real end afterwards still tears everything down.
  await h.end('other')
  expect(h.world.status).toBeUndefined()
})

test('a session that never recorded anything leaves no file at its end', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.end('other')
  expect(h.world.writes).toEqual([])
})

// ---------------------------------------------------------------------------------
// the welcome-back band

test('the band shows after idleMinutes of quiet, from the newest goal and decision', async ($, on) => {
  const h = harness($, on, { gitOut: ' M a.py\n?? b.ts\n' })
  await h.start()
  await h.turn('Port the billing module', 'Decision: use the new ledger', async () => {})
  expect((await h.band()).text).toBeUndefined()

  await h.world.clock.advance(29 * MIN)
  expect((await h.band()).text).toBeUndefined()
  await h.world.clock.advance(MIN)

  for (const surface of ['terminal', 'desktop'] as const) {
    const band = await h.band(surface)
    expect(band.text, surface).toBe(
      'Welcome back - you were on Port the billing module - last decision use the new ledger - 2 uncommitted files',
    )
    // The band wraps what the rest draws: the engine's own band is still there.
    expect(band.hasEngine).toBe(true)
  }
  expect(h.world.procCalls.every(c => c.argv.join(' ') === GIT.join(' '))).toBe(true)
  expect(h.world.procCalls[0]!.cwd).toBe(ROOT)
})

test('the next prompt dismisses the band, and it returns after another quiet spell', async ($, on) => {
  const h = harness($, on, { gitOut: '' })
  await h.start()
  await h.turn('First goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  expect((await h.band()).text).toMatch(/Welcome back/)

  await h.prompt('I am back')
  expect((await h.band()).text).toBeUndefined()

  await h.world.clock.advance(29 * MIN)
  expect((await h.band()).text).toBeUndefined()
  await h.world.clock.advance(2 * MIN)
  expect((await h.band()).text).toMatch(/Welcome back - you were on First goal/)
})

test('a finished turn restarts the idle clock', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Goal A', 'ok')
  await h.world.clock.advance(20 * MIN)
  await h.turn('Goal B', 'ok')
  await h.world.clock.advance(20 * MIN)
  expect((await h.band()).text).toBeUndefined()
  await h.world.clock.advance(11 * MIN)
  expect((await h.band()).text).toMatch(/you were on Goal B/)
})

test('idleMinutes is honoured', { options: { idleMinutes: 5 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Quick goal', 'ok')
  await h.world.clock.advance(4 * MIN)
  expect((await h.band()).text).toBeUndefined()
  await h.world.clock.advance(MIN)
  expect((await h.band()).text).toMatch(/Quick goal/)
})

// The engine itself refuses a value outside the manifest's 5-1440 (the module
// never loads), so the edges are the only values the module can be given.
test('idleMinutes accepts its upper edge', { options: { idleMinutes: 1440 } }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Day-long goal', 'ok')
  await h.world.clock.advance(1439 * MIN)
  expect((await h.band()).text).toBeUndefined()
  await h.world.clock.advance(MIN)
  expect((await h.band()).text).toMatch(/Day-long goal/)
})

test('an unset idleMinutes means 30', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Default goal', 'ok')
  await h.world.clock.advance(29 * MIN)
  expect((await h.band()).text).toBeUndefined()
  await h.world.clock.advance(MIN)
  expect((await h.band()).text).toMatch(/Default goal/)
})

test('the band needs something to say: no goal, no band', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.world.clock.advance(120 * MIN)
  expect((await h.band()).text).toBeUndefined()
})

test('a fresh session after a long break welcomes you back from the previous outbox', async ($, on) => {
  const old = [
    seedRow('p1', 'pending', { goal: 'Older goal', decisions: ['old decision one'] }),
    seedRow('p2', 'sent', { goal: 'Newest goal', decisions: [], ts: new Date(NOW0 - 40 * 60 * MIN).toISOString() }),
  ]
  const h = harness($, on, { files: startedOutbox('previous', old), gitOut: ' M x\n' })
  await h.start()
  const band = await h.band()
  expect(band.text).toBe(
    'Welcome back - you were on Newest goal - last decision old decision one - 1 uncommitted file',
  )
})

test('the decision segment is dropped when there is none', async ($, on) => {
  const h = harness($, on, { gitOut: '' })
  await h.start()
  await h.turn('No decisions here', 'ok')
  await h.world.clock.advance(31 * MIN)
  expect((await h.band()).text).toBe('Welcome back - you were on No decisions here - 0 uncommitted files')
})

test('without $.process the files segment is omitted and nothing throws', async ($, on) => {
  const h = harness($, on)
  h.world.procMode = 'deny'
  await h.start()
  await h.turn('Offline goal', 'Decision: stay offline')
  await h.world.clock.advance(31 * MIN)
  expect((await h.band()).text).toBe('Welcome back - you were on Offline goal - last decision stay offline')
})

test('a throwing $.process.run is survived as well', async ($, on) => {
  const h = harness($, on)
  h.world.procMode = 'throw'
  await h.start()
  await h.turn('Throw goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  expect((await h.band()).text).toBe('Welcome back - you were on Throw goal')
  // The outbox and the status line never needed it.
  expect(h.world.status).toBe('📮 clear')
})


test('a hung git status is raced and never piles up a second one', async ($, on) => {
  const h = harness($, on)
  h.world.procMode = 'hang'
  await h.start()
  await h.turn('Slow git goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  // The band still comes, without the files segment.
  expect((await h.band()).text).toBe('Welcome back - you were on Slow git goal')
  await h.turn('Another goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  expect((await h.band()).text).toBe('Welcome back - you were on Another goal')
  // Two refreshes, one still-running git: only one process was started.
  expect(h.world.procCalls).toHaveLength(1)
})

test('the band yields to a survey', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Survey goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  const ui = await $.ui.mount({ ...BAND, props: { ...BAND.props, hasSurvey: true }, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Welcome back/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /engine band/ })).toBeDefined()
  await ui.unmount()
})

test('the band sits beside a second plugin that draws its own Box (it wraps next)', { plugins: [pulseLike('append')] }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Wrapped goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Welcome back/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /pulse band/ })).toBeDefined()
  await ui.unmount()
})

// Known and accepted: when the other plugin is the outer hook and draws without
// next(e), our hook is never reached.
test('an outer plugin that draws without next hides the band (accepted limit)', { plugins: [pulseLike('prepend')] }, async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('Hidden goal', 'ok')
  await h.world.clock.advance(31 * MIN)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /pulse band/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Welcome back/ })).toBeUndefined()
  await ui.unmount()
})

// ---------------------------------------------------------------------------------
// the contract: no network, no subprocess but git status

test('the mod makes no network call and runs nothing but git status and the ledger emit', async ($, on) => {
  const h = harness($, on, { gitOut: ' M a\n' })
  await h.start()
  await h.turn('Everything', 'Decision: d', async () => {
    await h.edit('/repo/a.py')
    await h.todos([['T', 'completed']])
  })
  await h.run('bridge-note', 'a note')
  await $.session.compact({ trigger: 'auto', messages: MESSAGES })
  await h.world.clock.advance(120 * MIN)
  await h.band()
  await h.end('other')
  expect(h.world.network).toEqual([])
  for (const call of h.world.procCalls) expect(isGit(call.argv) || isEmit(call.argv)).toBe(true)
  expect(h.world.procCalls.some(call => isGit(call.argv))).toBe(true)
  expect(h.world.emits.length).toBe(2)
})

test('the store is only touched in memory-only mode', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('x', 'ok')
  expect(h.world.storeSets).toEqual([])
})

// ---------------------------------------------------------------------------------
// ledger replay: task and note rows go to `dopemux capture emit`, nothing else

type Harness = ReturnType<typeof harness>

const ALLOWED_EVENTS = ['task.completed', 'manual.memory_store']

// A main-loop turn that completes the given todo titles: one `task` row each.
async function finishTasks(h: Harness, titles: string[], text = 'ship') {
  await h.turn(text, 'ok', async () => {
    await h.todos(titles.map(t => [t, 'completed'] as [string, 'completed']))
  })
}

function sentCount(h: Harness): number {
  return h.rows().filter(r => r.state === 'sent').length
}

test('registers the bridge-note command in session.start and no other', async ($, on) => {
  const h = harness($, on)
  await h.start()
  expect(h.world.registered).toEqual([
    { name: 'bridge-note', description: 'Store a note in the capture ledger', argumentHint: '<text>' },
  ])
})

test('a completed todo is replayed once a minute later, with the exact argv and event', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['Ship the thing'])
  const row = h.rows().find(r => r.kind === 'task')!
  expect(row.state).toBe('pending')

  // Nothing runs before the tick.
  await h.world.clock.advance(59 * SEC)
  expect(h.world.emits).toHaveLength(0)

  await h.world.clock.advance(2 * SEC)
  expect(h.world.emits).toHaveLength(1)
  const call = h.world.procCalls.find(c => isEmit(c.argv))!
  expect(call.timeoutMs).toBe(LEDGER_TIMEOUT_MS)
  expect(call.argv.slice(0, 3)).toEqual(['dopemux', 'capture', 'emit'])
  expect(call.argv.slice(5)).toEqual(['--mode', 'plugin', '--repo-root', ROOT])
  expect(h.world.emits[0]!.event).toEqual({
    event_type: 'task.completed',
    payload: { title: 'Ship the thing' },
    ts_utc: row.ts,
    session_id: 's1',
    event_id: row.id,
  })
  const after = h.rows().find(r => r.id === row.id)!
  expect(after.state).toBe('sent')
  expect(after.attempts).toBe(1)
})

test('a row is marked sent only after exit 0: it is still pending while the call runs', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['Order matters'])
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits[0]!.rowStateAtCall).toBe('pending')
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('sent')
})

test('rows that are not task or note rows are never replayed', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.turn('only a goal', 'Decision: keep it local')
  await $.session.compact({ trigger: 'auto', messages: MESSAGES })
  await h.world.clock.advance(10 * MIN)
  expect(h.world.emits).toHaveLength(0)
  expect(h.world.procCalls.filter(c => isEmit(c.argv))).toHaveLength(0)
  expect(h.rows().every(r => r.state === 'pending')).toBe(true)
})

test('only task.completed and manual.memory_store are ever emitted', async ($, on) => {
  const stray = (id: string, intended: string) =>
    seedRow(id, 'pending', { session_id: 's1', kind: 'task', intended_event: intended, todos_completed: ['x'] })
  const h = harness($, on, {
    files: startedOutbox('s1', [
      stray('aaaaaaaaaaaaaaaaaaaaaaaa', 'decision.logged'),
      stray('bbbbbbbbbbbbbbbbbbbbbbbb', 'work.untracked_detected'),
    ]),
  })
  await h.start()
  await finishTasks(h, ['Real task'])
  await h.run('bridge-note', 'a real note')
  await h.world.clock.advance(5 * MIN)
  expect(h.world.emits.length).toBe(2)
  for (const emit of h.world.emits) expect(ALLOWED_EVENTS).toContain(emit.event.event_type)
  // The stray rows were never touched.
  const stays = h.rows().filter(r => r.id.startsWith('aaaa') || r.id.startsWith('bbbb'))
  expect(stays.map(r => r.state)).toEqual(['pending', 'pending'])
})

test('a non-zero exit leaves the row pending, counts the attempt and says the ledger is unavailable', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.ledgerMode = 'fail'
  await finishTasks(h, ['Stuck'])
  await h.world.clock.advance(61 * SEC)
  const row = h.rows().find(r => r.kind === 'task')!
  expect(row.state).toBe('pending')
  expect(row.attempts).toBe(1)
  expect(h.world.status).toBe('📮 1 pending (ledger unavailable)')

  // The ledger comes back: the next tick delivers it and the suffix goes.
  h.world.ledgerMode = 'ok'
  await h.world.clock.advance(61 * SEC)
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('sent')
  expect(h.world.status).toBe('📮 clear')
})

test('a timed-out call leaves the row pending and is not joined by a second call', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.ledgerMode = 'slow'
  await finishTasks(h, ['Slow one'])
  await h.world.clock.advance(61 * SEC) // the call starts
  expect(h.world.emits).toHaveLength(1)
  await h.world.clock.advance(20 * SEC) // the 15 s guard gave up
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('pending')
  expect(h.rows().find(r => r.kind === 'task')!.attempts).toBe(1)
  expect(h.world.status).toBe('📮 1 pending (ledger unavailable)')

  // Still hung: several ticks pass and no second call overlaps it.
  await h.world.clock.advance(5 * MIN)
  expect(h.world.emits).toHaveLength(1)
  expect(h.world.ledgerMaxActive).toBe(1)

  // The hung call finally returns exit 0: the next tick may run again.
  h.world.ledgerMode = 'ok'
  await h.world.clock.advance(6 * MIN)
  expect(h.world.ledgerMaxActive).toBe(1)
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('sent')
})

for (const mode of ['deny', 'throw'] as const) {
  test(`without a usable $.process (${mode}) rows stay pending, nothing throws and attempts are not spent`, async ($, on) => {
    const h = harness($, on)
    h.world.procMode = mode
    await h.start()
    await finishTasks(h, ['Offline task'])
    await h.run('bridge-note', 'offline note')
    await h.world.clock.advance(5 * MIN)
    const rows = h.rows().filter(r => r.intended_event !== null)
    expect(rows).toHaveLength(2)
    expect(rows.every(r => r.state === 'pending' && r.attempts === 0)).toBe(true)
    expect(h.world.status).toBe('📮 2 pending (ledger unavailable)')
    // The outbox itself kept working.
    expect(h.rows().filter(r => r.kind === 'turn')).toHaveLength(1)
    expect(h.world.network).toEqual([])
  })
}

test('at most three rows go out per tick', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['t1', 't2', 't3', 't4', 't5'])
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits).toHaveLength(3)
  expect(sentCount(h)).toBe(3)
  await h.world.clock.advance(60 * SEC)
  expect(h.world.emits).toHaveLength(5)
  expect(sentCount(h)).toBe(5)
  // Nothing pending to send: the timer is not re-armed.
  await h.world.clock.advance(10 * MIN)
  expect(h.world.emits).toHaveLength(5)
})

test('calls are serial: a slow ledger never has two in flight', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.ledgerMode = 'slow'
  await finishTasks(h, ['s1', 's2', 's3', 's4'])
  await h.world.clock.advance(61 * SEC)
  await h.world.clock.advance(30 * MIN)
  expect(h.world.ledgerMaxActive).toBe(1)
  expect(h.world.emits.length).toBeGreaterThan(0)
})

test('after five failed attempts a row is dead: not retried, counted in the status line', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.ledgerMode = 'fail'
  await finishTasks(h, ['Doomed'])
  for (let i = 0; i < 8; i += 1) await h.world.clock.advance(61 * SEC)
  const row = h.rows().find(r => r.kind === 'task')!
  expect(row.state).toBe('dead')
  expect(row.attempts).toBe(5)
  expect(h.world.emits).toHaveLength(5)
  expect(h.world.status).toBe('⚠ 1 undeliverable')

  // A dead row stays in the file and is never sent again.
  h.world.ledgerMode = 'ok'
  await h.world.clock.advance(10 * MIN)
  expect(h.world.emits).toHaveLength(5)
})

test('a fresh session counts dead rows it finds on disk', async ($, on) => {
  const h = harness($, on, {
    files: startedOutbox('old', [seedRow('dddddddddddddddddddddddd', 'dead', { kind: 'task', intended_event: 'task.completed' })]),
  })
  await h.start()
  expect(h.world.status).toBe('⚠ 1 undeliverable')
})

test('a resend carries the same event_id every time, and again after a restart', async ($, on) => {
  const h = harness($, on)
  await h.start()
  h.world.ledgerMode = 'fail'
  await finishTasks(h, ['Same id'])
  const row = h.rows().find(r => r.kind === 'task')!
  await h.world.clock.advance(61 * SEC)
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits.map(e => e.event.event_id)).toEqual([row.id, row.id])
  expect(h.world.emits[0]!.event).toEqual(h.world.emits[1]!.event)
})

test('a pending row left by an earlier run of the same session is replayed with its stored id', async ($, on) => {
  const stored = seedRow('cccccccccccccccccccccccc', 'pending', {
    session_id: 's1',
    kind: 'task',
    intended_event: 'task.completed',
    todos_completed: ['Left behind'],
  })
  const h = harness($, on, { files: startedOutbox('s1', [stored]) })
  await h.start()
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits).toHaveLength(1)
  expect(h.world.emits[0]!.event).toMatchObject({
    event_type: 'task.completed',
    event_id: 'cccccccccccccccccccccccc',
    payload: { title: 'Left behind' },
  })
  expect(h.rows().find(r => r.id === stored.id)!.state).toBe('sent')
})

test('rows of other sessions are not replayed (single writer per file)', async ($, on) => {
  const h = harness($, on, {
    files: startedOutbox('other', [
      seedRow('eeeeeeeeeeeeeeeeeeeeeeee', 'pending', { kind: 'task', intended_event: 'task.completed', todos_completed: ['theirs'] }),
    ]),
  })
  await h.start()
  await h.world.clock.advance(10 * MIN)
  expect(h.world.emits).toHaveLength(0)
})

test('a malformed task row with no title is dead at once and nothing is sent for it', async ($, on) => {
  const h = harness($, on, {
    files: startedOutbox('s1', [
      seedRow('ffffffffffffffffffffffff', 'pending', { session_id: 's1', kind: 'task', intended_event: 'task.completed' }),
    ]),
  })
  await h.start()
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits).toHaveLength(0)
  expect(h.rows().find(r => r.id.startsWith('ffff'))!.state).toBe('dead')
})

test('replay still runs for the old session after /clear changes the session id', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['Before clear'])
  h.world.sid = 's2' // /clear: a fresh session id, no session.start
  await $.session.end({ reason: 'clear', sessionId: 's1', resume: { sessionId: 's1' } as never })
  await h.world.clock.settle()
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits).toHaveLength(1)
  expect(h.world.emits[0]!.event.session_id).toBe('s1')
  expect(h.rows('s1').find(r => r.kind === 'task')!.state).toBe('sent')
})

test('a real session end cancels the replay timer', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['Never sent'])
  await h.end('other')
  await h.world.clock.advance(10 * MIN)
  expect(h.world.emits).toHaveLength(0)
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('pending')
})

test('without <root>/.dopemux the rows replay from memory and the store follows', async ($, on) => {
  const h = harness($, on, { dopemux: false })
  await h.start()
  await finishTasks(h, ['Memory task'])
  expect(h.world.status).toBe('📮 memory-only')
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits).toHaveLength(1)
  const saved = h.world.store.get('outbox:s1') as { rows: Row[] }
  expect(saved.rows.find(r => r.kind === 'task')!.state).toBe('sent')
})

test('a replay write that fails is retried and never surfaces', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['Write trouble'])
  h.world.writeMode = 'fail'
  await h.world.clock.advance(61 * SEC)
  expect(h.world.status).toBe('⚠ outbox write failed')
  h.world.writeMode = 'ok'
  await h.turn('later', 'ok')
  expect(h.rows().find(r => r.kind === 'task')!.state).toBe('sent')
})

// --- /bridge-note ----------------------------------------------------------------------

test('bridge-note queues a note row and says queued, not stored', async ($, on) => {
  const h = harness($, on)
  await h.start()
  const answer = await h.run('bridge-note', '  remember   the milk  ')
  expect(answer.text).toMatch(/queued/i)
  expect(answer.text).toMatch(/nothing is stored yet/i)
  expect(answer.text).not.toMatch(/\b(?:note|it) (?:is|was|has been) stored\b/i)
  const note = h.rows().find(r => r.kind === 'note')!
  expect(note).toMatchObject({
    note: 'remember the milk',
    intended_event: 'manual.memory_store',
    state: 'pending',
    attempts: 0,
    todos_completed: [],
    decisions: [],
  })
  expect(h.world.status).toBe('📮 1 pending')
})

test('bridge-note is replayed as manual.memory_store with the stable id', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.run('bridge-note', 'a note for later')
  const note = h.rows().find(r => r.kind === 'note')!
  await h.world.clock.advance(61 * SEC)
  expect(h.world.emits).toHaveLength(1)
  expect(h.world.emits[0]!.event).toEqual({
    event_type: 'manual.memory_store',
    payload: { category: 'implementation', entry_type: 'manual_note', summary: 'a note for later' },
    ts_utc: note.ts,
    session_id: 's1',
    event_id: note.id,
  })
  expect(h.rows().find(r => r.kind === 'note')!.state).toBe('sent')
})

test('bridge-note redacts secrets and caps the text at 500 characters', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.run('bridge-note', 'key sk-ant-api03-ABCDEFGHIJKLMNOP mail me@example.com DATABASE_URL=postgres://u:pw@h/db')
  const first = h.rows().find(r => r.kind === 'note')!
  expect(first.note).not.toMatch(/ABCDEFGHIJKLMNOP|me@example\.com|pw@h/)
  expect(first.note).toContain('[REDACTED')

  await h.run('bridge-note', 'x'.repeat(900))
  const notes = h.rows().filter(r => r.kind === 'note')
  expect(notes).toHaveLength(2)
  expect(notes[1]!.note!.length).toBe(500)
})

test('bridge-note with no text returns usage and appends nothing', async ($, on) => {
  const h = harness($, on)
  await h.start()
  for (const args of ['', '   ', '\n\t']) {
    const answer = await h.run('bridge-note', args)
    expect(answer.text).toMatch(/usage/i)
    expect(answer.text).toMatch(/nothing/i)
  }
  expect(h.rows()).toHaveLength(0)
  expect(h.world.writes).toHaveLength(0)
})

test('two identical notes are two rows', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await h.run('bridge-note', 'same')
  await h.run('bridge-note', 'same')
  expect(h.rows().filter(r => r.kind === 'note')).toHaveLength(2)
})

test('bridge-note works when $.process is missing: queued, nothing thrown', async ($, on) => {
  const h = harness($, on)
  h.world.procMode = 'deny'
  await h.start()
  const answer = await h.run('bridge-note', 'offline note')
  expect(answer.text).toMatch(/queued/i)
  await h.world.clock.advance(3 * MIN)
  expect(h.rows().find(r => r.kind === 'note')!.state).toBe('pending')
})

test('no HTTP call is made anywhere in a full run, and no decision.logged is emitted', async ($, on) => {
  const h = harness($, on)
  await h.start()
  await finishTasks(h, ['A', 'B'])
  await h.run('bridge-note', 'n')
  await h.turn('d', 'Decision: x')
  await h.world.clock.advance(10 * MIN)
  await h.end('other')
  expect(h.world.network).toEqual([])
  const types = h.world.emits.map(e => e.event.event_type)
  expect(types.sort()).toEqual(['manual.memory_store', 'task.completed', 'task.completed'])
})
