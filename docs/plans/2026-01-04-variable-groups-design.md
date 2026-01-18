# Variable Group Support Design

**Date**: 2026-01-04
**Status**: Approved

## Overview

Update the tennis doubles tournament manager to support 2-5 groups per tournament (instead of hardcoded 2 groups), add tournament history navigation, and improve the UI to handle variable group counts.

## Context

Currently the system is hardcoded for exactly 2 groups: "Racketeers" and "Serve-ivors". The next tournament round will have 3-5 groups, requiring the system to be more flexible. Additionally, users should be able to view previous tournaments, which is not currently supported.

## Requirements

1. Support 2-5 groups per tournament (minimum 2 for backward compatibility)
2. Groups use creative names from a predefined pool (no numbers or ranking indicators)
3. Tournament history page with prev/next navigation between tournaments
4. Header displays tournament name instead of hardcoded group names
5. Tab colors extend to support up to 5 groups

## Design Decisions

### 1. Data Model & Group Pool

**Existing Model**: No schema changes needed. The current `Group` and `TournamentGroup` models already support variable groups through their many-to-many relationship.

**Predefined Group Pool**: Create 6-8 tennis-themed group names as Group records:
- Racketeers (existing)
- Serve-ivors (existing)
- Smashers
- Volleyers
- Lobbers
- Baseliners
- Net Rushers
- Groundstrokers

These will be created via a data migration. Admins select 2-5 of these when setting up each tournament.

**Validation**: Add Tournament model validation:
- Minimum 2 groups per tournament
- Maximum 5 groups per tournament
- Clear error messages when outside this range

### 2. UI Updates for Variable Groups

**Tab Colors**: Extend tailwind config from 2 to 5 tab badge colors:
- `tab-badge-0`: Blue tone (existing)
- `tab-badge-1`: Pink tone (existing)
- `tab-badge-2`: Green/teal tone (new)
- `tab-badge-3`: Purple/lavender tone (new)
- `tab-badge-4`: Orange/amber tone (new)

Colors must be added to both `extend.colors` and `safelist` in tailwind.config.js.

**Tab Rendering**: The grid.html template already loops dynamically through groups. The `group_index` (0-4) maps to `tab-badge-{index}` color classes.

**Header Update**: Change header template from hardcoded "The Racketeers & Serve-ivors" to dynamically display tournament name:
```html
<h1>{{ tournament.name }}</h1>
```

### 3. Tournament History & Navigation

**URL Structure**:
- `/` - Home page (current/latest ongoing tournament)
- `/tournament/<tournament_id>/` - View specific tournament grid
- `/tournaments/` - Tournament history page

**History Page Features**:
- List all tournaments in reverse chronological order
- Display tournament name, dates, and status (Ongoing/Completed)
- Each tournament clickable to view its grid
- Prev/Next arrows for chronological navigation when viewing a specific tournament

**Navigation Implementation**:
- Prev/Next arrows appear in grid template (above tabs or near header)
- Prev = older tournament, Next = newer tournament
- Arrows disabled/hidden at boundaries (oldest/newest tournament)
- Links point to `/tournament/<adjacent_id>/`

### 4. Admin Interface Updates

**Tournament Admin**:
- Keep existing inline `TournamentGroup` interface
- Group dropdown shows predefined pool names
- Set inline to show 5 empty forms by default
- Add help text: "Select 2-5 groups for this tournament from the predefined pool"
- Validation enforces 2-5 group requirement with clear error messages

**Group Management**:
- Groups created once via data migration
- Admins select from existing Group records, don't create new ones
- New group names added via Django admin's Group model if needed in future

**Backward Compatibility**: Existing 2-group tournaments continue working. Validation applies to new/edited tournaments.

## Implementation Summary

**Changes Required**:

1. **Data Migration**: Create predefined Group records
2. **Models**: Add 2-5 group validation to Tournament model
3. **Tailwind Config**: Add tab-badge-2, tab-badge-3, tab-badge-4 colors
4. **Templates**:
   - Update header to show tournament name
   - Add prev/next navigation to grid template
   - Create tournament history list template
5. **Views & URLs**:
   - Pass tournament object to grid template
   - Add tournament history list view
   - Add specific tournament detail view (with tournament_id parameter)
   - Add URL routes for new views
6. **Admin**: Add inline formset validation and help text

**Testing Considerations**:
- Test with 2, 3, 4, and 5 groups
- Verify tab colors for all group counts
- Test prev/next navigation at boundaries
- Ensure existing 2-group tournaments display correctly
- Verify admin validation messages
- Test tournament history page with multiple tournaments

## Architecture Notes

This design leverages the existing flexible data model. The Tournament-Group relationship was already designed to support multiple groups; the system was just using it in a constrained way. By removing UI and validation constraints, we enable the full flexibility the data model already provides.
