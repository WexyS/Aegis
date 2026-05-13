import { StoreName } from './schemas';

export interface Migration {
  version: number;
  description: string;
  up: (db: IDBDatabase, transaction: IDBTransaction) => Promise<void>;
}

export const MIGRATIONS: Migration[] = [
  {
    version: 1,
    description: "Initial Schema Creation",
    up: async (db, tx) => {
      // The baseline schema logic, assuming it's done via onupgradeneeded.
      // This is a placeholder for actual data manipulation if needed.
    }
  },
  {
    version: 2,
    description: "Upgrade RuntimeEvents to support Replay causality (sequence_num, span_id, causation_id)",
    up: async (db, tx) => {
      console.log("[MIGRATOR] Running v1 -> v2 Migration: Backfilling missing causality fields.");
      const store = tx.objectStore(StoreName.EVENTS);
      const request = store.openCursor();
      
      return new Promise((resolve, reject) => {
        request.onsuccess = (event: any) => {
          const cursor = event.target.result;
          if (cursor) {
            const data = cursor.value;
            let modified = false;
            
            // Add default sequence_num if missing
            if (typeof data.payload?.sequence_num !== 'number') {
              data.payload = data.payload || {};
              data.payload.sequence_num = 0; // Baseline
              modified = true;
            }
            // Add span_id if missing
            if (!data.payload?.span_id) {
              data.payload = data.payload || {};
              data.payload.span_id = 'legacy-span-' + Date.now();
              modified = true;
            }
            
            if (modified) {
              const updateReq = cursor.update(data);
              updateReq.onerror = () => {
                console.error(`[MIGRATOR] Failed to migrate event ${data.id}`);
              };
            }
            cursor.continue();
          } else {
            resolve();
          }
        };
        request.onerror = () => reject(request.error);
      });
    }
  }
];

export class MigrationEngine {
  public static async runMigrations(db: IDBDatabase, oldVersion: number, newVersion: number, transaction: IDBTransaction) {
    console.log(`[MIGRATOR] DB Upgrade detected: v${oldVersion} -> v${newVersion}`);
    
    // Sort migrations and apply sequentially
    const pendingMigrations = MIGRATIONS
      .filter(m => m.version > oldVersion && m.version <= newVersion)
      .sort((a, b) => a.version - b.version);
      
    if (pendingMigrations.length === 0) {
      console.log("[MIGRATOR] No data migrations required.");
      return;
    }

    try {
      for (const migration of pendingMigrations) {
        console.log(`[MIGRATOR] Executing Migration v${migration.version}: ${migration.description}`);
        await migration.up(db, transaction);
      }
      console.log("[MIGRATOR] All migrations completed successfully.");
    } catch (err) {
      console.error("[MIGRATOR] FATAL: Migration failed. Replay integrity may be compromised.", err);
      // In a strict environment, we might dispatch an event to quarantine the DB.
      throw err;
    }
  }
}
