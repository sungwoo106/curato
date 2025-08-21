# Qwen Model Integration for Place Selection

## Overview
This document summarizes the changes made to transition from using the Phi model to the Qwen model for place selection in the edge-day-planner application.

## Changes Made

### 1. New Qwen Prompt Function (`core/prompts.py`)
- **Added**: `build_qwen_location_prompt()` function
- **Purpose**: Generates prompts for Qwen model to select 4-5 places from candidate list
- **Format**: Uses ChatML format (`<|im_start|>`, `<|im_end|>`) that Qwen expects
- **Functionality**: Identical to Phi prompt but with Qwen-compatible formatting

### 2. New Qwen Route Planner Method (`preferences.py`)
- **Added**: `run_qwen_route_planner()` method
- **Purpose**: Replaces Phi model calls for place selection
- **Features**: 
  - Uses Qwen model via `runner.run_qwen(prompt, "qwen_place_selection_profile")`
  - Calls `_extract_places_from_qwen_output()` for parsing
  - Maintains same fallback logic and error handling

### 3. New Qwen Output Parser (`preferences.py`)
- **Added**: `_extract_places_from_qwen_output()` method
- **Purpose**: Parses Qwen model output to extract selected places
- **Functionality**: Identical to Phi parser since both models use same output format

### 4. Modified Existing Method (`preferences.py`)
- **Updated**: `run_route_planner()` method
- **Changes**: 
  - All Phi model calls commented out (preserved for easy restoration)
  - Now calls `run_qwen_route_planner()` instead
  - Maintains same interface and return values

### 5. Updated Imports (`preferences.py`)
- **Added**: Import for `build_qwen_location_prompt`
- **Maintains**: All existing imports for backward compatibility

### 6. Updated Progress Messages (`generate_plan.py`)
- **Modified**: Progress messages to reflect Qwen usage
- **Updated**: Console output to show "with Qwen" for clarity

## Profile File Naming

To avoid conflicts with story generation profiling, the Qwen model uses different profile file names:

- **Place Selection**: `qwen_place_selection_profile` 
- **Itinerary Generation**: `qwen_itinerary_profile`

This prevents overlap when both functions are running simultaneously.

## How to Switch Back to Phi

To restore Phi model usage, simply:

1. **Uncomment Phi calls** in `run_route_planner()` method
2. **Comment out** the call to `run_qwen_route_planner()`
3. **Restore** the original Phi model execution code

Example:
```python
# Comment out this line:
# return self.run_qwen_route_planner()

# Uncomment all the Phi model calls above
```

## Benefits of Qwen Integration

1. **Consistent Model Usage**: Both place selection and itinerary generation now use Qwen
2. **Better Performance**: Qwen may provide more consistent place selection
3. **Unified Prompt Format**: Both functions now use ChatML format
4. **Easy Rollback**: Phi functionality preserved and easily restorable

## Testing

The integration has been completed and tested to ensure:
- ✅ Qwen prompt generation works correctly
- ✅ All imports function properly  
- ✅ Prompt format matches Qwen requirements
- ✅ Korean place names are preserved
- ✅ All validation checks pass
- ✅ Phi model code preserved as comments (not deleted)
- ✅ Unique profile file names prevent conflicts

## Usage

The application now automatically uses Qwen for place selection when calling:
```python
planner = Preferences(...)
route_plan = planner.run_route_planner()  # Now uses Qwen instead of Phi
```

No changes are required in the calling code - the interface remains identical.
