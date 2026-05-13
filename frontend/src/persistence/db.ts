// src/persistence/db.ts

import { DB_NAME, DB_VERSION, StoreName } from './schemas';
import { MigrationEngine } from './migrations';

export class AegisDB {
  private db: IDBDatabase | null = null;

  public async init(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = async (event: any) => {
        const db = event.target.result;
        
        // 1. Structural Schema Updates
        if (!db.objectStoreNames.contains(StoreName.SESSIONS)) {
          db.createObjectStore(StoreName.SESSIONS, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(StoreName.MESSAGES)) {
          db.createObjectStore(StoreName.MESSAGES, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(StoreName.EVENTS)) {
          const eventStore = db.createObjectStore(StoreName.EVENTS, { keyPath: 'id' });
          eventStore.createIndex('sessionId', 'sessionId', { unique: false });
          eventStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
        if (!db.objectStoreNames.contains(StoreName.SNAPSHOTS)) {
          db.createObjectStore(StoreName.SNAPSHOTS, { keyPath: 'id' });
        }

        // 2. Data Migrations
        const oldVersion = event.oldVersion;
        const newVersion = event.newVersion || DB_VERSION;
        if (oldVersion < newVersion && oldVersion !== 0) {
          try {
            await MigrationEngine.runMigrations(db, oldVersion, newVersion, event.target.transaction);
          } catch (e) {
            console.error("[DB] Migration failed during onupgradeneeded.", e);
            // In a real scenario, we might want to throw to abort the upgrade transaction
          }
        }
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve(request.result);
      };

      request.onerror = () => reject(request.error);
    });
  }

  public async put(storeName: StoreName, data: any): Promise<void> {
    if (!this.db) await this.init();
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.put(data);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  public async get(storeName: StoreName, key: string): Promise<any> {
    if (!this.db) await this.init();
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  public async getAll(storeName: StoreName, indexName?: string, indexValue?: any): Promise<any[]> {
    if (!this.db) await this.init();
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      
      let request;
      if (indexName && indexValue) {
        const index = store.index(indexName);
        request = index.getAll(indexValue);
      } else {
        request = store.getAll();
      }

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

export const aegisDB = new AegisDB();
