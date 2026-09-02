import { loadConfig } from "./config.js";
import type { ControlPlaneStore } from "./core/store.js";
import { buildServer, startupFailure } from "./http/server.js";
import { MemoryRunDispatcher, RedisRunDispatcher, type RunDispatcher } from "./infra/dispatcher.js";
import { MemoryStore } from "./stores/memory-store.js";
import { PostgresStore } from "./stores/postgres-store.js";

async function main(): Promise<void> {
  const config = loadConfig();
  let store: ControlPlaneStore;
  let dispatcher: RunDispatcher;

  if (config.store === "postgres") {
    store = new PostgresStore(config.databaseUrl!);
    dispatcher = new RedisRunDispatcher(
      config.redisUrl,
      config.jobSigningSecret,
      config.internalCallbackBaseUrl,
    );
  } else {
    store = new MemoryStore();
    dispatcher = new MemoryRunDispatcher();
    if (config.devAuth) await store.setTenantPlan("dev-tenant", "business");
  }
  await store.migrate();
  const app = await buildServer({ config, store, dispatcher });
  await app.listen({ host: config.host, port: config.port });

  let closing = false;
  const shutdown = async (signal: string): Promise<void> => {
    if (closing) return;
    closing = true;
    app.log.info({ signal }, "JySecAI control plane shutting down");
    const forcedExit = setTimeout(() => {
      process.stderr.write("JySecAI shutdown exceeded 15 seconds\n");
      process.exit(1);
    }, 15_000);
    forcedExit.unref();
    try {
      await app.close();
    } finally {
      clearTimeout(forcedExit);
    }
  };
  process.once("SIGINT", () => void shutdown("SIGINT"));
  process.once("SIGTERM", () => void shutdown("SIGTERM"));
}

main().catch(startupFailure);
