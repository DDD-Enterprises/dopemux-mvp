import type { PlannerExtension, PlannerExtensionModule } from './extensionTypes';

type ModuleMap = Record<string, unknown>;

function isExtensionModule(value: unknown): value is PlannerExtensionModule {
  if (!value || typeof value !== 'object' || !('default' in value)) return false;
  const extension = (value as { default?: unknown }).default;
  return Boolean(
    extension &&
      typeof extension === 'object' &&
      typeof (extension as PlannerExtension).id === 'string' &&
      (extension as PlannerExtension).id.length > 0 &&
      typeof (extension as PlannerExtension).render === 'function',
  );
}

export function loadExtensions(modules: ModuleMap): readonly PlannerExtension[] {
  const byId = new Map<string, PlannerExtension>();
  for (const [path, module] of Object.entries(modules)) {
    if (!isExtensionModule(module)) throw new Error(`Malformed planner extension export: ${path}`);
    const extension = module.default;
    if (byId.has(extension.id)) throw new Error(`Duplicate planner extension id: ${extension.id}`);
    byId.set(extension.id, extension);
  }
  const encoder = new TextEncoder();
  const compareBytes = (left: string, right: string) => {
    const a = encoder.encode(left);
    const b = encoder.encode(right);
    for (let index = 0; index < Math.min(a.length, b.length); index += 1) {
      if (a[index] !== b[index]) return a[index] - b[index];
    }
    return a.length - b.length;
  };
  return [...byId.values()].sort((left, right) => compareBytes(left.id, right.id));
}

const discoveredModules = import.meta.glob('./extensions/*.tsx', { eager: true });
export const plannerExtensions = loadExtensions(discoveredModules);
