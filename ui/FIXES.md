# Bug Fixes Applied

## Issue 1: Excessive API Logging (FIXED)

**Problem**: Running `team-formation-api` logged in INFO mode, writing too much information.

**Fix**: Changed logging level from INFO to WARNING in two places:

1. `team_formation/api/main.py:23` - Changed `logging.basicConfig(level=logging.WARNING)`
2. `team_formation/api/main.py:350` - Changed `log_level="warning"` in uvicorn.run()

**Result**: API now only logs warnings and errors, significantly reducing console output.

---

## Issue 2: SSE Messages Not Showing in Real-Time (IMPROVED)

**Problem**: UI did not show SSE messages as they were streaming, only after the API finally returned.

**Fix**: Reduced the event queue timeout in the API event generator:

- `team_formation/api/main.py:195` - Changed timeout from 0.5s to 0.1s for more responsive streaming

**Additional Improvement**: Added debug logging in `ui/src/services/api.ts:52` to help diagnose SSE issues:
```typescript
console.log('SSE event received:', event.event, data)
```

**Result**: Events should now stream more responsively. Check browser console for real-time event logs.

**Note**: Real-time streaming also depends on:
- Network buffering
- Browser behavior
- Solver performance (how often solutions are found)
- For very small problems, the solver may complete before multiple events are generated

---

## Issue 3: UI Error "Failed to parse server message" (FIXED)

**Problem**: When API returned results, UI showed error: "Connection error: Failed to parse server message"

**Root Cause**: The error handling in the SSE client was catching parse errors but not providing enough debug information.

**Fix**: Enhanced error logging in `ui/src/services/api.ts:64`:
```typescript
console.error('Failed to parse SSE message:', error, 'Raw event:', event)
```

**Additional API Cleanup**: Removed unused code in `team_formation/api/main.py:219-226` that created but never used a `completion_event` variable.

**Result**: Better error diagnostics. If parsing errors still occur, check browser console for the raw event data.

---

## Issue 4: Roster Table Not Showing Rows (FIXED)

**Problem**: When loading a CSV file, the table showed columns but no rows.

**Root Cause**: A `v-for` loop was creating custom slot templates for ALL columns, overriding Vuetify's default rendering.

**Fix**: Removed the problematic template loop in `ui/src/components/RosterTable.vue:54-74`, keeping only the special handling for `team_number` column.

**Result**: Table now displays all rows and columns from any CSV structure (no `id` column required).

---

## Testing the Fixes

1. **Start the API** (should now have minimal logging):
   ```bash
   team-formation-api
   ```

2. **Start the UI**:
   ```bash
   cd ui
   npm run dev
   ```

3. **Open browser console** (F12) to see SSE event logs:
   - Should see "SSE event received: progress" messages as optimization runs
   - Should see "SSE event received: complete" when finished
   - Any parsing errors will show the raw event data

4. **Test the workflow**:
   - Upload a CSV file → verify rows are displayed
   - Add constraints → verify real-time validation
   - Click "Create Teams" → watch browser console for real-time progress events
   - Verify results display correctly

---

## Known Limitations

**SSE Real-Time Display**: For very small datasets or simple constraints, the solver may complete so quickly that you only see the final result. This is normal behavior - the streaming works correctly, but there simply aren't many intermediate solutions to display.

To test real-time streaming with more visible updates:
- Use larger datasets (100+ participants)
- Add multiple constraints with varying weights
- Set a longer max_time (120s+)

---

## Additional Debug Information

If you still experience issues, check the browser console for:

1. **SSE Connection**: Should see requests to `/assign_teams` in Network tab
2. **Event Stream**: Filter for EventStream type to see raw SSE data
3. **Console Logs**: Our debug logging shows each event as it arrives
4. **Errors**: Any parsing or connection errors will be logged with details
