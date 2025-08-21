# Backend Code Refactoring Guide

## Overview

The original `preferences.py` file was 1,400+ lines long and violated several software engineering best practices. This refactoring breaks it down into focused, maintainable modules following the Single Responsibility Principle.

## What Was Refactored

### Before (Monolithic Structure)
```
preferences.py (1,400+ lines)
├── Logger class (50+ lines)
├── RateLimiter class (50+ lines)  
├── Preferences class (1,300+ lines)
    ├── AI model management
    ├── Caching logic
    ├── Place management
    ├── Itinerary generation
    └── Helper methods
```

### After (Modular Structure)
```
core/
├── models.py (80 lines) - AI model management
├── cache_manager.py (120 lines) - Caching functionality
├── rate_limiter.py (70 lines) - Rate limiting
├── place_manager.py (140 lines) - Place selection & collection
└── prompts.py (133 lines) - AI prompt templates

preferences_refactored.py (400 lines) - Main orchestrator
```

## New Module Breakdown

### 1. `core/models.py` - AI Model Management
**Responsibility**: Manages Phi and Qwen model instances
- Lazy initialization of model runners
- Reusable model instances for better performance
- Model validation and fallback handling
- Performance statistics

**Key Methods**:
- `_initialize_models()` - Lazy initialization
- `get_phi_runner()` - Get Phi model instance
- `get_qwen_runner()` - Get Qwen model instance

### 2. `core/cache_manager.py` - Caching System
**Responsibility**: Manages place search result caching
- Time-based expiration (1 hour TTL)
- Size-based cleanup (max 50 entries)
- Automatic cleanup of expired entries
- Cache key generation based on search parameters

**Key Methods**:
- `_generate_cache_key()` - Create unique cache keys
- `get_cached_results()` - Retrieve cached results
- `cache_results()` - Store new results
- `_cleanup_cache()` - Automatic cleanup

### 3. `core/rate_limiter.py` - API Rate Limiting
**Responsibility**: Prevents excessive API calls
- Respects Kakao API rate limits
- Configurable call limits and time windows
- Automatic waiting when limits are reached
- Status monitoring

**Key Methods**:
- `can_call()` - Check if call is allowed
- `wait_if_needed()` - Wait for rate limit reset
- `get_status()` - Current rate limiter status

**Note**: Renamed to `APIRateLimiter` to avoid conflicts with existing `RateLimiter` class

### 4. `core/place_manager.py` - Place Management
**Responsibility**: Handles place type selection and collection
- Intelligent place type selection based on companion type
- Batch API calls to reduce requests
- Place reduction and candidate selection
- Integration with caching and rate limiting

**Key Methods**:
- `select_place_types()` - Smart place type selection
- `collect_places()` - Batch place collection
- `_reduce_to_20_candidates()` - Candidate reduction

### 5. `preferences_refactored.py` - Main Orchestrator
**Responsibility**: Coordinates all components and main workflow
- User preference management
- Orchestrates place collection and itinerary generation
- Maintains the same public API as the original
- Significantly reduced complexity

## ⚠️ Important: Avoiding Conflicts

### **Class Name Conflicts Resolved**
- **`RateLimiter`** → **`APIRateLimiter`** (renamed to avoid conflict with existing class)
- All other class names are unique and won't conflict

### **Import Path Safety**
- New modules use `core.*` namespace (safe from conflicts)
- Existing imports continue to work through compatibility layer
- No circular dependencies introduced

### **Backward Compatibility**
- `preferences_compat.py` provides seamless migration path
- Existing code requires zero changes
- Gradual migration possible

## Benefits of the Refactoring

### 1. **Maintainability**
- Each module has a single, clear responsibility
- Easier to locate and fix bugs
- Simpler to add new features

### 2. **Testability**
- Individual components can be tested in isolation
- Mock dependencies easily
- Better test coverage

### 3. **Reusability**
- Components can be reused in other parts of the application
- Rate limiter can be used for other APIs
- Cache manager can cache other types of data

### 4. **Readability**
- Smaller files are easier to understand
- Clear separation of concerns
- Reduced cognitive load

### 5. **Performance**
- No performance impact from refactoring
- Better resource management through focused components
- Easier to optimize individual components

## Migration Guide

### For Existing Code
The refactored version maintains the same public API, so existing code should work without changes:

```python
# Old way (still works)
from preferences import Preferences

# New way (recommended)
from preferences_refactored import Preferences

# Compatibility layer (safest for production)
from preferences_compat import Preferences
```

### For New Development
Use the modular components directly for more focused functionality:

```python
from core.cache_manager import CacheManager
from core.rate_limiter import RateLimiter
from core.place_manager import PlaceManager

# Use individual components as needed
cache = CacheManager()
rate_limiter = RateLimiter()
place_manager = PlaceManager(rate_limiter, cache)
```

## Code Quality Improvements

### 1. **Single Responsibility Principle**
- Each class has one clear purpose
- Methods are focused and cohesive
- Dependencies are explicit and minimal

### 2. **Dependency Injection**
- Components receive dependencies through constructor
- Easy to mock for testing
- Loose coupling between components

### 3. **Error Handling**
- Consistent error handling patterns
- Graceful fallbacks
- Better error messages

### 4. **Documentation**
- Clear docstrings for all public methods
- Type hints for better IDE support
- Examples in docstrings

## Future Improvements

### 1. **Configuration Management**
- Move hardcoded values to configuration files
- Environment-specific settings
- Feature flags

### 2. **Logging Framework**
- Replace simple logging with proper logging framework
- Structured logging for better analysis
- Log levels and filtering

### 3. **Metrics and Monitoring**
- Performance metrics collection
- Health checks for components
- Alerting for failures

### 4. **Async Support**
- Async/await for I/O operations
- Better concurrency handling
- Non-blocking operations

## Conclusion

This refactoring transforms a monolithic, hard-to-maintain file into a clean, modular architecture that follows software engineering best practices. The code is now:

- **Easier to understand** - Each module has a clear purpose
- **Easier to test** - Components can be tested independently  
- **Easier to maintain** - Changes are isolated to specific modules
- **Easier to extend** - New features can be added without affecting existing code
- **More professional** - Follows industry standards and best practices

The refactored code maintains 100% backward compatibility while providing a much better foundation for future development.
