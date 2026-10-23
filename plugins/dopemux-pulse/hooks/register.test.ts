import type { On, RenderElement } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine, MockClock } from 'claude-code/testing'

const MIN = 60_000
const URL = 'http://127.0.0.1:3025/api/v1/state'

const BAND = {
  plugin: 'dopemux-pulse',
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

type Behaviour =
  | { kind: 'ok'; body: unknown }
  | { kind: 'raw'; text: string }
  | { kind: 'status'; code: number }
  | { kind: 'down' }
  | { kind: 'slow' }
  | { kind: 'slow-then-deny' }

// Everything beneath the plugin is mocked here: the clock, the engine's HTTP
// answer, and the display calls the plugin makes (recorded, never drawn).
// `denyCommand` makes `command.register` refuse that one name.
function harness($: Engine, on: On, first: Behaviour, denyCommand?: string) {
  const clock: MockClock = mock.clock(on)
  const world = {
    clock,
    behaviour: first,
    statuses: [] as (string | undefined)[],
    toasts: [] as string[],
    urls: [] as string[],
    registered: [] as string[],
    get status() {
      return world.statuses[world.statuses.length - 1]
    },
  }

  // Beneath the plugin the engine draws its own band; a hook that passes
  // (`next(e)`) therefore shows this text.
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return h$(Text, 'engine band')
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))
  on('command.register', (_, e) => {
    if (e.name === denyCommand) return { deny: 'refused' }
    world.registered.push(e.name)
    return { value: { command: e.name } }
  })
  on('ui.status', (_, e) => {
    world.statuses.push(e.text)
    return { value: undefined }
  })
  on('ui.toast', (_, e) => {
    world.toasts.push(e.text)
    return { value: undefined }
  })
  on('http.fetch', async (_, e) => {
    world.urls.push(e.url)
    const b = world.behaviour
    if (b.kind === 'down') return { deny: 'connection refused' }
    if (b.kind === 'slow-then-deny') {
      await clock.sleep(10 * MIN)
      return { deny: 'connection reset' }
    }
    if (b.kind === 'slow') await clock.sleep(10 * MIN)
    const status = b.kind === 'status' ? b.code : 200
    const text =
      b.kind === 'ok' ? JSON.stringify(b.body) : b.kind === 'raw' ? b.text : ''
    return {
      value: { status, ok: status >= 200 && status < 300, headers: {}, text },
    }
  })

  return {
    world,
    set: (b: Behaviour) => {
      world.behaviour = b
    },
    async start() {
      await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
      await clock.settle()
    },
    async end(reason: 'clear' | 'resume' | 'logout' | 'prompt_input_exit' | 'other' = 'other') {
      await $.session.end({
        reason,
        sessionId: 's1',
        resume: { sessionId: 's1' } as never,
      })
      await clock.settle()
    },
    async run(command: string, args = '') {
      return $.command.run({
        command,
        args,
        origin: { kind: 'composer' },
        presentation: { isFullscreen: false, columns: 80 },
      })
    },
  }
}

const HEALTHY = { kind: 'ok', body: { energy: 'medium', attention: 'focused' } } as const

test('status line shows energy, attention and mod-counted session minutes', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  expect(h.world.urls[0]).toBe(URL)
  expect(h.world.status).toBe('🎯 idle · ⚡ medium · 🧠 focused · ⏱ 0m')

  await h.world.clock.advance(61 * MIN)
  expect(h.world.status).toBe('🎯 idle · ⚡ medium · 🧠 focused · ⏱ 61m')
})

test('status line falls back to the alias keys', async ($, on) => {
  const h = harness($, on, {
    kind: 'ok',
    body: { energy_level: 'low', attention_state: 'scattered', session_minutes: 0 },
  })
  await h.start()
  expect(h.world.status).toBe('🎯 idle · ⚡ low · 🧠 scattered · ⏱ 0m')
})

test('the current keys win over the aliases', async ($, on) => {
  const h = harness($, on, {
    kind: 'ok',
    body: { energy: 'high', attention: 'focused', energy_level: 'low', attention_state: 'scattered' },
  })
  await h.start()
  expect(h.world.status).toBe('🎯 idle · ⚡ high · 🧠 focused · ⏱ 0m')
})

test('status line says so when the engine is down, errors or answers garbage', async ($, on) => {
  const h = harness($, on, { kind: 'down' })
  await h.start()
  expect(h.world.status).toBe('🎯 idle · 🔌 ADHD engine unreachable · ⏱ 0m')

  h.set({ kind: 'status', code: 503 })
  await h.world.clock.advance(MIN)
  expect(h.world.status).toBe('🎯 idle · 🔌 ADHD engine unreachable (HTTP 503) · ⏱ 1m')

  h.set({ kind: 'raw', text: '<html>not json</html>' })
  await h.world.clock.advance(MIN)
  expect(h.world.status).toBe('🎯 idle · ⚠ ADHD engine state malformed · ⏱ 2m')

  h.set({ kind: 'ok', body: { energy: 7, attention: null } })
  await h.world.clock.advance(MIN)
  expect(h.world.status).toBe('🎯 idle · ⚠ ADHD engine state malformed · ⏱ 3m')

  h.set({ kind: 'ok', body: { energy: 'low' } })
  await h.world.clock.advance(MIN)
  expect(h.world.status).toBe('🎯 idle · ⚡ low · 🧠 ? · ⏱ 4m')
})

test('a hung engine times out instead of wedging the poll', async ($, on) => {
  const h = harness($, on, { kind: 'slow' })
  await h.start()
  await h.world.clock.advance(2_100)
  expect(h.world.status).toBe('🎯 idle · 🔌 ADHD engine unreachable · ⏱ 0m')
})

// F1: the 2 s timeout only changes what the status line shows. The request it
// gave up on is still outstanding, and no poll may start another until it ends.
test('T1: a timed-out request still pending holds the guard, no second fetch', async ($, on) => {
  const h = harness($, on, { kind: 'slow' })
  await h.start()
  await h.world.clock.advance(2_100)
  expect(h.world.status).toBe('🎯 idle · 🔌 ADHD engine unreachable · ⏱ 0m')
  expect(h.world.urls).toHaveLength(1)

  await h.world.clock.advance(5 * MIN)
  expect(h.world.urls).toHaveLength(1)
})

test('T2: once the abandoned request settles, polling resumes and a healthy answer shows', async ($, on) => {
  const h = harness($, on, { kind: 'slow' })
  await h.start()
  await h.world.clock.advance(2_100)
  h.set(HEALTHY)

  // The engine is healthy again, but the first request is still outstanding.
  await h.world.clock.advance(7 * MIN)
  expect(h.world.urls).toHaveLength(1)
  expect(h.world.status).toBe('🎯 idle · 🔌 ADHD engine unreachable · ⏱ 0m')

  // Past the settle (10 min) and a tick: not pinned to an exact count.
  await h.world.clock.advance(12 * MIN - 2_100 - 7 * MIN)
  expect(h.world.urls.length).toBeGreaterThanOrEqual(2)
  expect(h.world.status).toMatch(/⚡ medium · 🧠 focused/)

  // The stale answer of the abandoned request was never shown or toasted; the
  // only toast is the recovery one, from the healthy poll after the settle.
  expect(h.world.statuses.some(t => /malformed/.test(t ?? ''))).toBe(false)
  expect(h.world.toasts).toEqual(['ADHD engine is back'])
})

test('T3: a request that is refused late raises nothing and changes nothing', async ($, on) => {
  // An unhandled rejection is not observable from here (no `process` in the
  // sandbox); the runner itself fails the file with "a rejection nothing
  // handled", so a late deny that escaped would turn this file red.
  const h = harness($, on, { kind: 'slow-then-deny' })
  await h.start()
  await h.world.clock.advance(2_100)
  expect(h.world.status).toBe('🎯 idle · 🔌 ADHD engine unreachable · ⏱ 0m')
  const statuses = h.world.statuses.length

  // Up to just past the 10 min settle: the late deny lands and writes nothing.
  // At most the tick after the settle starts one new (again pending) request,
  // whose own 2 s timeout has not yet elapsed.
  await h.world.clock.advance(10 * MIN - 2_100 + 1_000)
  expect(h.world.urls.length).toBeLessThanOrEqual(2)
  expect(h.world.statuses).toHaveLength(statuses)
  expect(h.world.toasts).toEqual([])
})

test('T4: a session that ends while a request is pending stays silent when it settles', async ($, on) => {
  const h = harness($, on, { kind: 'slow' })
  await h.start()
  await h.world.clock.advance(2_100)
  await h.end()

  const urls = h.world.urls.length
  const statuses = h.world.statuses.length
  const toasts = h.world.toasts.length
  await h.world.clock.advance(15 * MIN)

  expect(h.world.urls).toHaveLength(urls)
  expect(h.world.statuses).toHaveLength(statuses)
  expect(h.world.toasts).toHaveLength(toasts)
})

// F6: a refused registration is told to the person, once per name, and the
// rest of the setup carries on.
test('T5: a refused command registration is toasted and the rest still starts', async ($, on) => {
  const h = harness($, on, HEALTHY, 'break')
  await h.start()

  expect(h.world.registered).toEqual(['pulse-focus', 'done'])
  expect(h.world.toasts).toEqual(['dopemux-pulse: /break could not be registered'])
  expect(h.world.urls).toHaveLength(1)
  expect(h.world.status).toBe('🎯 idle · ⚡ medium · 🧠 focused · ⏱ 0m')
})

test('toasts once on up to down and once on recovery, not every poll', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  expect(h.world.toasts).toEqual([])

  h.set({ kind: 'down' })
  await h.world.clock.advance(MIN)
  await h.world.clock.advance(MIN)
  await h.world.clock.advance(MIN)
  expect(h.world.toasts).toEqual(['ADHD engine unreachable'])

  h.set(HEALTHY)
  await h.world.clock.advance(MIN)
  await h.world.clock.advance(MIN)
  expect(h.world.toasts).toEqual(['ADHD engine unreachable', 'ADHD engine is back'])
})

test('an engine that was never up is one status line, not a toast', async ($, on) => {
  const h = harness($, on, { kind: 'down' })
  await h.start()
  await h.world.clock.advance(3 * MIN)
  expect(h.world.toasts).toEqual([])
})

// `/focus` is a name Claude Code ships; `$.command.register` refuses it, so the
// mod serves the focus clock as `/pulse-focus`.
test('registers /pulse-focus, /break and /done and never a built-in name', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  expect(h.world.registered).toEqual(['pulse-focus', 'break', 'done'])
})

test('/pulse-focus defaults to 25 minutes and the band counts it down', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  const answer = await h.run('pulse-focus')
  expect(answer.text).toMatch(/25/)

  await h.world.clock.advance(10 * MIN)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /15 min left/ }))?.text).toMatch(/of 25/)
  await ui.unmount()

  await h.world.clock.advance(MIN)
  expect(h.world.status).toBe('🎯 11/25 · ⚡ medium · 🧠 focused · ⏱ 11m')
})

test('/pulse-focus takes 5-120 minutes and refuses the rest', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  for (const bad of ['4', '0', '-5', '121', '1000', 'abc', '12.5', '25 30']) {
    const answer = await h.run('pulse-focus', bad)
    expect(answer.text, `args "${bad}"`).toMatch(/5-120/)
  }
  // Nothing started: the band is idle.
  await h.world.clock.advance(MIN)
  expect(h.world.status).toMatch(/^🎯 idle/)

  for (const [good, left] of [['5', 5], ['120', 120], [' 45 ', 45]] as const) {
    await h.run('pulse-focus', good)
    const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: new RegExp(`${left} min left`) })).toBeDefined()
    await ui.unmount()
  }
})

test('a toast at the limit, then a gentler nudge at 90 continuous minutes', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  await h.run('pulse-focus', '5')
  await h.world.clock.advance(4 * MIN)
  expect(h.world.toasts).toEqual([])
  await h.world.clock.advance(MIN)
  expect(h.world.toasts).toHaveLength(1)
  expect(h.world.toasts[0]).toMatch(/5-minute focus block is up/)

  // Past the limit and still no /break: the band says so.
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /\/break/ })).toBeDefined()
  await ui.unmount()

  // Chaining blocks without a break keeps the continuous-focus clock running.
  await h.run('pulse-focus', '120')
  await h.world.clock.advance(84 * MIN)
  expect(h.world.toasts).toHaveLength(1)
  await h.world.clock.advance(MIN)
  expect(h.world.toasts).toHaveLength(2)
  expect(h.world.toasts[1]).toMatch(/90 minutes/)

  // Neither toast repeats.
  await h.world.clock.advance(60 * MIN)
  expect(h.world.toasts.filter(t => /90 minutes/.test(t))).toHaveLength(1)
})

test('/break and /done end the block and cancel its toasts', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  await h.run('pulse-focus', '5')
  const broke = await h.run('break')
  expect(broke.text).toMatch(/break/i)
  await h.world.clock.advance(10 * MIN)
  expect(h.world.toasts).toEqual([])

  await h.run('pulse-focus', '5')
  const done = await h.run('done')
  expect(done.text).toMatch(/done/i)
  await h.world.clock.advance(10 * MIN)
  expect(h.world.toasts).toEqual([])

  // With nothing running, both say so rather than failing.
  expect((await h.run('done')).text).toMatch(/no focus block/i)
  expect((await h.run('break')).text).toMatch(/break/i)
})

test('a break resets the 90-minute continuous-focus clock', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  await h.run('pulse-focus', '60')
  await h.world.clock.advance(60 * MIN)
  await h.run('break')
  await h.run('pulse-focus', '60')
  await h.world.clock.advance(60 * MIN)
  expect(h.world.toasts.filter(t => /90 minutes/.test(t))).toEqual([])
})

test('session.end cancels the poll and every focus timer', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  await h.run('pulse-focus', '5')

  await h.end()
  const polls = h.world.urls.length
  const toasts = h.world.toasts.length
  await h.world.clock.advance(200 * MIN)

  expect(h.world.urls).toHaveLength(polls)
  expect(h.world.toasts).toHaveLength(toasts)
})

for (const reason of ['resume', 'logout', 'prompt_input_exit'] as const) {
  test(`session.end (${reason}) cancels the poll and the focus timers`, async ($, on) => {
    const h = harness($, on, HEALTHY)
    await h.start()
    await h.run('pulse-focus', '5')
    await h.end(reason)
    const polls = h.world.urls.length
    const toasts = h.world.toasts.length
    await h.world.clock.advance(200 * MIN)
    expect(h.world.urls).toHaveLength(polls)
    expect(h.world.toasts).toHaveLength(toasts)
  })
}

// /clear ends the conversation but not the process: session.end fires with
// reason 'clear' and no session.start follows, so the mod must keep running.
test('session.end with reason clear leaves the poll, status and focus block running', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  await h.run('pulse-focus', '5')

  await h.end('clear')
  expect(h.world.status).toBeDefined()

  // The next poll still happens and still updates the status line.
  const polls = h.world.urls.length
  h.set({ kind: 'ok', body: { energy: 'low', attention: 'scattered' } })
  await h.world.clock.advance(MIN)
  expect(h.world.urls.length).toBeGreaterThan(polls)
  expect(h.world.status).toBe('🎯 1/5 · ⚡ low · 🧠 scattered · ⏱ 1m')

  // The focus block survived: the band still counts it and the limit toast fires.
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /4 min left of 5/ })).toBeDefined()
  await ui.unmount()
  await h.world.clock.advance(4 * MIN)
  expect(h.world.toasts.filter(t => /5-minute focus block is up/.test(t))).toHaveLength(1)

  // And a real end afterwards still cancels everything.
  await h.end('other')
  const after = h.world.urls.length
  await h.world.clock.advance(200 * MIN)
  expect(h.world.urls).toHaveLength(after)
})

test('the 90-minute nudge survives a /clear', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  await h.run('pulse-focus', '120')
  await h.end('clear')
  await h.world.clock.advance(90 * MIN)
  expect(h.world.toasts.filter(t => /90 minutes/.test(t))).toHaveLength(1)
})

test('the band is idle (next) when no focus block runs', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /engine band/ }))?.text).toBe('engine band')
  expect(await ui.find({ type: 'Text', text: /min left/ })).toBeUndefined()
  await ui.unmount()
})

test('the band yields to a survey and to a settled idle state after /done', async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  await h.run('pulse-focus')
  let ui = await $.ui.mount({ ...BAND, props: { ...BAND.props, hasSurvey: true }, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /engine band/ })).toBeDefined()
  await ui.unmount()

  await h.run('done')
  ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /engine band/ })).toBeDefined()
  await ui.unmount()
})

test('the plugin makes no call beyond one GET of the configured URL', async ($, on) => {
  const h = harness($, on, HEALTHY)
  on('process.run', () => {
    throw new Error('the mod must not run processes')
  })
  await h.start()
  await h.run('pulse-focus')
  await h.world.clock.advance(30 * MIN)
  expect(new Set(h.world.urls)).toEqual(new Set([URL]))
})

test('the engine URL option is honoured and a trailing slash is dropped', { options: { engineUrl: 'http://10.0.0.5:9999/' } }, async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  expect(h.world.urls[0]).toBe('http://10.0.0.5:9999/api/v1/state')
})

test('a non-http engine URL is refused and nothing is fetched', { options: { engineUrl: 'file:///etc/passwd' } }, async ($, on) => {
  const h = harness($, on, HEALTHY)
  await h.start()
  expect(h.world.urls).toEqual([])
  expect(h.world.status).toBe('🎯 idle · ⚠ ADHD engine URL is not http(s) · ⏱ 0m')
})

// `h` (the JSX factory) is a global the engine provides; a .ts test calls it
// directly. Named h$ so it does not collide with the harness variable `h`.
function h$(tag: Parameters<typeof h>[0], ...children: unknown[]) {
  return h(tag, null, ...children) as RenderElement
}
