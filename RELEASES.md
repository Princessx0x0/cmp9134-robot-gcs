# Release Management — CMP9134 Robot GCS

## Semantic Versioning Scenarios

Current live version: **v1.2.3**

### Scenario A — Bug fix: robot crash below 0% battery
**Next version: v1.2.4**
This is a PATCH increment. The fix corrects an internal error without changing
any API inputs or outputs. Existing clients are unaffected and no new features
are added. PATCH is incremented when backwards-compatible bug fixes are made.

### Scenario B — New /api/history endpoint added
**Next version: v1.3.0**
This is a MINOR increment. A new endpoint is added but all existing endpoints
continue to work exactly as before. Clients that don't use the new endpoint
are completely unaffected. MINOR is incremented when new backwards-compatible
functionality is added. PATCH resets to 0.

### Scenario C — Breaking change to /api/move payload
**Next version: v2.0.0**
This is a MAJOR increment. Old frontends sending the previous payload format
will receive 422 errors — this is a breaking change. Any client must update
their integration. MAJOR is incremented when incompatible API changes are made.
MINOR and PATCH both reset to 0.

---

## Release History

### v1.0.0 — Initial Release
- FastAPI backend with robot status and move endpoints
- RobotClient implementing Singleton and Facade patterns
- Docker Compose stack with robot simulator
- GitHub Actions CI pipeline with automated testing
- 23 unit and integration tests passing
- Legacy stats module refactored with Pydantic validation
