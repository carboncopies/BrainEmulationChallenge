# NES-API Versioning

**Author:** Swastik Behera  
**Date:** 2026-08-23  
**Branch:** `feature/nes-api-versioning`

---

## What was broken

- BrainGenix-NES, BrainGenix-API, PythonClient and BrainEmulationChallenge could run mismatched versions with no warning
- The internal API↔NES handshake compared calendar build dates (`2024.04.10`) not protocol versions
- Python client had a `GetAPIVersion()` method but never called it on connect — `GetClientVersion()` returned a hardcoded stale string (`"2024.2.23"`)

---

## Part 1 — Manual version check

### What I added

- `NES_API_VERSION "1.0.0"` constant in both `Version.h.in` files (separate from the build date)
- `GetAPIVersion()` in both C++ repos now returns `NES_API_VERSION` instead of `VERSION`
- The version comparison in `ClientManager.cpp` and `SafeClient.cpp` updated to match against `NES_API_VERSION`
- `/Diagnostic/Version` REST endpoint now returns `NESAPIVersion` field
- PythonClient `Setup()` now calls `CheckAPIVersion()` on every connection — raises a clear error if server is too old

**Error example:**
```
PythonClient requires NES-API >= 1.0.0 but the connected server provides NES-API 0.9.0.
Please update BrainGenix-NES/BrainGenix-API to a compatible version.
```

### Files changed

| Repo | File |
|------|------|
| BrainGenix-NES | `CMake/CompileInfo/VersioningSystem/Version.h.in` |
| BrainGenix-NES | `Source/Core/RPC/StaticRoutes.cpp` |
| BrainGenix-NES | `Source/Core/RPC/SafeClient.cpp` |
| BrainGenix-API | `CMake/Scripts/VersioningSystem/Version.h.in` |
| BrainGenix-API | `Source/Core/RPC/StaticRoutes.cpp` |
| BrainGenix-API | `Source/Core/RPC/ClientManager.cpp` |
| BrainGenix-API | `Source/Core/Resource/Controller.h` |
| PythonClient | `BrainGenix/NES/Client/Client.py` |

---

## Part 2 — Checksum-based version check

### What I added

NES automatically collects every registered route name and hashes the sorted list using FNV-1a 64-bit — same algorithm in both C++ and Python so both sides compute independently.

- `RouteNames_` vector in `RPCManager` — `AddRoute()` appends every sub-route name to it
- `ComputeChecksum()` and `GetManifestJSON()` methods on `RPCManager`
- Two new RPC routes: `GetAPIChecksum` and `GetAPIManifest`
- API gateway fetches checksum and manifest from NES during handshake, stores in `Server` struct
- REST `/Diagnostic/Version` now returns `APIChecksum` and `APIManifest`
- PythonClient has `_KNOWN_ROUTES` (80 routes), computes same hash locally, compares on connect
- On mismatch: diffs the two manifests and names the exact routes that differ

**Error example:**
```
API Checksum Mismatch — route sets differ between client and server.
  Routes on server NOT known to this client: ['Simulation/NewFeature']
  Update PythonClient._KNOWN_ROUTES or use a matching BrainGenix-NES version.
```

### Files changed

| Repo | File |
|------|------|
| BrainGenix-NES | `Source/Core/RPC/RPCManager.h` |
| BrainGenix-NES | `Source/Core/RPC/RPCManager.cpp` |
| BrainGenix-API | `Source/Core/Server/Server.h` |
| BrainGenix-API | `Source/Core/RPC/ClientManager.cpp` |
| BrainGenix-API | `Source/Core/Resource/Controller.h` |
| PythonClient | `BrainGenix/NES/Client/Client.py` |

---

## Tests

### Local (no server needed)

| Test | Result |
|------|--------|
| `_parse_version` handles valid, zero, garbage input | PASS |
| Compatible versions pass, old server rejected with correct message | PASS |
| FNV-1a deterministic, 16 hex chars | PASS |
| Checksum is order-independent | PASS |
| Adding a route changes the checksum | PASS |
| `_KNOWN_ROUTES` (80 routes) → checksum `8398ef003e9649cd` | PASS |

### Live server (NES port 8011, API port 8010)

| Test | Result |
|------|--------|
| `/Diagnostic/Version` returns `NESAPIVersion: "1.0.0"` | PASS |
| `/Diagnostic/Version` returns `APIChecksum` and `APIManifest` | PASS |
| Server checksum matches Python client checksum (`8398ef003e9649cd`) | PASS |
| Both sides have exactly 80 routes, no diff | PASS |
| Simulated extra server route caught with named diff | PASS |

---

## How versioning works going forward

| Event | Action |
|-------|--------|
| New route added to NES | Bump MINOR in both `Version.h.in` files; add route to `_KNOWN_ROUTES` in PythonClient |
| Existing route changed or removed | Bump MAJOR in both `Version.h.in` files; update `_KNOWN_ROUTES` |
| Bug fix, no interface change | Bump PATCH |
