import sqlite3
import json
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "riksahyak.db")

class MockDocumentReference:
    def __init__(self, collection_name: str, doc_id: str):
        self.collection_name = collection_name
        self.doc_id = doc_id
        
    def _get_table(self):
        if self.collection_name == "rides": return "rides", "id"
        if self.collection_name == "drivers": return "drivers", "driver_id"
        if self.collection_name == "users": return "users", "user_id"
        return "counters", "name" # Fallback for settings
        
    def get(self):
        table, id_col = self._get_table()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            if table == "counters":
                res = conn.execute("SELECT data FROM settings WHERE id = ?", (self.doc_id,)).fetchone()
            else:
                res = conn.execute(f"SELECT data FROM {table} WHERE {id_col} = ?", (self.doc_id,)).fetchone()
            
            if res:
                return MockDocumentSnapshot(True, self.doc_id, json.loads(res["data"]))
            return MockDocumentSnapshot(False, self.doc_id, {})
        except Exception:
            return MockDocumentSnapshot(False, self.doc_id, {})
        finally:
            conn.close()
            
    def update(self, data: dict):
        snap = self.get()
        if snap.exists:
            merged = snap.to_dict()
            merged.update(data)
            self.set(merged)
            
    def set(self, data: dict, merge: bool = False):
        table, id_col = self._get_table()
        conn = sqlite3.connect(DB_PATH)
        try:
            if table == "counters":
                conn.execute("CREATE TABLE IF NOT EXISTS settings (id TEXT PRIMARY KEY, data JSON)")
                if merge:
                    existing = self.get()
                    if existing.exists:
                        merged = existing.to_dict()
                        merged.update(data)
                        data = merged
                conn.execute("INSERT OR REPLACE INTO settings (id, data) VALUES (?, ?)", (self.doc_id, json.dumps(data)))
            else:
                # We only implement update for rides/drivers
                pass
            conn.commit()
        finally:
            conn.close()

class MockDocumentSnapshot:
    def __init__(self, exists: bool, doc_id: str, data: dict):
        self.exists = exists
        self.id = doc_id
        self._data = data
    def to_dict(self):
        return self._data

class MockQuery:
    def __init__(self, collection_name: str, filters: list = None):
        self.collection_name = collection_name
        self.filters = filters or []
        
    def where(self, field, op, value):
        self.filters.append((field, op, value))
        return self
        
    def stream(self):
        table = self.collection_name
        if table not in ["rides", "drivers", "users"]:
            return []
            
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            res = conn.execute(f"SELECT data FROM {table}").fetchall()
            docs = []
            for row in res:
                data = json.loads(row["data"])
                # Apply filters manually
                match = True
                for f, op, v in self.filters:
                    if op == "==" and data.get(f) != v:
                        match = False
                        break
                if match:
                    docs.append(MockDocumentSnapshot(True, data.get("id", ""), data))
            return docs
        except Exception:
            return []
        finally:
            conn.close()

class MockCollectionReference(MockQuery):
    def document(self, doc_id: str):
        return MockDocumentReference(self.collection_name, doc_id)

class MockFirestore:
    def collection(self, name: str):
        return MockCollectionReference(name)

def get_db():
    return MockFirestore()

def initialize_firebase():
    pass
