import { loadScannerAdapterConfig } from "./config.js";
import { buildScannerAdapter } from "./server.js";

async function main(): Promise<void> {
  const config = loadScannerAdapterConfig();
  const app = await buildScannerAdapter(config);
  const stop = async () => {
    await app.close();
  };
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);
  await app.listen({ host: config.host, port: config.port });
}

main().catch((error) => {
  process.stderr.write(`JySecAI scanner adapter failed: ${error instanceof Error ? error.message : String(error)}\n`);
  process.exit(1);
});
