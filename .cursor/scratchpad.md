# Clara Engine Project Status

## Background and Motivation
Clara Engine is a multi-tenant AI bot platform enabling deployment of personalized GPT-powered Twitter bots for multiple clients from a single, centralized codebase. The system needs to be robust, scalable, and maintainable.

## Stakeholder Requirements (Updated)

### Rate Limits & Scale
- OpenAI: 50 completions/day per client
- Twitter: 10 tweets/day per client
- Hard cap: 1 GPT request/sec per client
- Initial scale: 5 clients × 3 tweets/day ≈ 15 tweets/day total

### Critical Monitoring Metrics
1. GPT tokens used (per-client + global)
2. Tweet-post success/failure count
3. Engine-loop runtime & error rate
4. Redis queue depth (rate-limit queue)

### Recovery Objectives
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes
- Implementation: Supabase backups + Render redeploy

## 7-Day Implementation Plan

### Day 1-2: OpenAI Rate Limiting & Monitoring
1. Token Bucket Rate Limiter
   - [ ] Implement RedisRateLimiter class
   - [ ] Add per-client and global rate limits
   - [ ] Create rate limit middleware
   Success Criteria:
   - Enforces 1 req/sec per client
   - Handles concurrent requests safely
   - Proper error handling & retries

2. Cost & Token Monitoring
   - [ ] Set up Prometheus metrics
   - [ ] Add token usage tracking
   - [ ] Implement cost estimation
   Success Criteria:
   - Real-time token usage visible
   - Cost tracking per client
   - Alerting on quota approach

3. A/B Testing Framework
   - [ ] Add prompt variant support
   - [ ] Implement hash-based splitting
   - [ ] Create variant tracking
   Success Criteria:
   - Consistent variant assignment
   - Performance tracking
   - Easy variant management

### Day 3-5: Main Engine Loop
1. Scheduler Core
   - [ ] Implement TimeSlotManager
   - [ ] Add timezone handling
   - [ ] Create posting window logic
   Success Criteria:
   - Respects client posting_hours
   - Handles timezone correctly
   - Maintains last_posted_at

2. Client Rotation System
   - [ ] Create ClientRotator class
   - [ ] Add fairness mechanisms
   - [ ] Implement backoff handling
   Success Criteria:
   - Fair resource distribution
   - Respects rate limits
   - Handles errors gracefully

3. Error Recovery & Metrics
   - [ ] Add retry mechanisms
   - [ ] Implement circuit breakers
   - [ ] Create metrics collection
   Success Criteria:
   - Automatic error recovery
   - Clear error reporting
   - Complete metrics coverage

### Day 6-7: Twitter Integration Scaffold
1. Interface Design
   - [ ] Create TwitterClient class
   - [ ] Define error hierarchy
   - [ ] Add rate limit types
   Success Criteria:
   - Clean, documented API
   - Comprehensive error types
   - Ready for real credentials

2. Mock Implementation
   - [ ] Add tweet posting logic
   - [ ] Implement rate limiting
   - [ ] Create test suite
   Success Criteria:
   - Full mock coverage
   - Tests passing
   - ≥90% code coverage

## Current Focus
MVP Development for 5 Initial Clients:
- Target: Working prototype with basic UI dashboard
- Scale: 5 clients × 3 tweets/day ≈ 15 tweets/day
- Core Features: Tweet generation & posting, basic scheduling, simple monitoring, essential UI

## MVP Requirements (Prioritized)
1. Must Have ✅
   - Basic tweet generation with OpenAI
   - Simple time-based posting
   - Per-client rate limiting
   - Basic error handling
   - Essential UI Features:
     * Client login/authentication
     * Simple dashboard with tweet status
     * Basic configuration management
     * Activity monitoring

2. Nice to Have (Post-MVP) 🔄
   - A/B testing
   - Advanced monitoring
   - Complex scheduling
   - Performance optimization
   - Advanced UI Features:
     * Analytics dashboard
     * Advanced configuration
     * Prompt management UI
     * User management

## Next Immediate Steps (MVP Focus)
1. Essential UI Implementation (2-3 days)
   - [ ] Set up Next.js project structure
   - [ ] Implement Supabase Auth
   - [ ] Create basic dashboard layout
   - [ ] Add essential pages:
     * Login page
     * Dashboard overview
     * Tweet status view
     * Basic settings
   Success Criteria:
   - Clients can log in securely
   - View tweet status and history
   - Manage basic configuration
   - Monitor activity

2. Complete Main Tweet Generation Loop (2 days)
   - [ ] Create simple scheduler (single-threaded, time-based)
   - [ ] Implement basic tweet generation flow
   - [ ] Add simple posting mechanism
   Success Criteria:
   - Can generate tweets for each client
   - Respects basic time windows
   - Handles rate limits

3. Basic Twitter Integration (1-2 days)
   - [ ] Implement minimal TwitterClient
   - [ ] Add simple tweet posting
   - [ ] Basic error handling
   Success Criteria:
   - Can post tweets
   - Handles API errors
   - Respects rate limits

4. Simple Monitoring (1 day)
   - [ ] Add basic logging
   - [ ] Track tweet success/failure
   - [ ] Monitor rate limits
   Success Criteria:
   - Can track system status
   - Basic error alerting
   - Usage monitoring

## Implementation Strategy
1. UI First Approach
   - Start with authentication and basic UI
   - Simple, clean dashboard design
   - Essential configuration forms
   - Real-time status updates

2. Simplify First Version
   - Use single-threaded processing
   - Simple round-robin client rotation
   - Basic time-window checking
   - File-based logging

3. Minimal Viable Schema
   - Clients table (existing)
   - Tweets table (existing)
   - Simple status tracking
   - User authentication tables

4. Basic Error Handling
   - Retry on common errors
   - Skip problematic clients
   - Log issues for review
   - Surface errors in UI

## Technical Stack (UI)
1. Frontend
   - Next.js 14 (App Router)
   - Tailwind CSS
   - Supabase Auth
   - React Query

2. API Layer
   - Next.js API Routes
   - Supabase Client
   - Type-safe endpoints

3. Authentication
   - Supabase Auth
   - Role-based access
   - Secure session management

## Post-MVP Improvements
1. UI Enhancements
   - Advanced analytics dashboard
   - Rich configuration interface
   - User management system
   - Prompt template editor

2. Optimization Phase
   - Multi-threading
   - Advanced scheduling
   - Performance tuning
   - A/B testing

3. Monitoring Expansion
   - Prometheus metrics
   - Detailed analytics
   - Advanced alerting
   - Dashboard creation

4. Feature Enhancement
   - Complex scheduling
   - Content optimization
   - Advanced error recovery
   - Client management UI

## Executor's Feedback or Assistance Requests
- Need to set up Redis for rate limiting
- Need to configure Prometheus for metrics
- Need to define A/B testing data schema

## Lessons
1. Always include info useful for debugging in the program output
2. Read files before editing them
3. Run npm audit before proceeding with dependency updates
4. Always ask before using the -force git command
5. Ensure proper error handling and logging in all API integrations

## Technical Dependencies
1. Prometheus setup
   - Basic metrics configuration
   - Grafana dashboard templates
   - Alert rules definition

2. A/B Testing Schema
   - Variant definition format
   - Performance metrics storage
   - Assignment algorithm design

3. Scheduler Components
   - Time slot calculation logic
   - Timezone conversion utilities
   - Window validation rules

## Current Status / Progress Tracking

### Completed Features ✅
1. Project Structure and Setup
   - Basic project structure established
   - Development environment configuration
   - CI/CD pipeline with GitHub Actions
   - Pre-commit hooks and code quality tools
   - Documentation templates

2. Database Integration
   - Supabase integration complete
   - Initial schema migrations
   - Database client implementation
   - CRUD operations for clients and tweets
   - Row-level security policies

3. OpenAI Integration Core Components
   - OpenAIClient implementation with Azure support
   - Prompt management system
   - Response validation with safety checks
   - Semantic caching system
   - Comprehensive test coverage

### In Progress 🚀
1. UI Development (Priority)
   - Next.js project setup
   - Supabase Auth integration
   - Basic dashboard implementation
   - Client configuration interface

2. OpenAI Integration (Final Touches)
   - Rate limiting implementation
   - Basic monitoring system
   - Simple error handling

3. Twitter Integration
   - Basic client implementation
   - Tweet posting functionality
   - Error handling

### Pending Tasks 📋
1. Essential UI Features (MVP)
   - [ ] Authentication & Login
     * Supabase Auth setup
     * Login/logout flow
     * Session management
     * Success Criteria: Secure client login working

   - [ ] Dashboard Overview
     * Tweet status display
     * Basic stats view
     * Activity feed
     * Success Criteria: Clients can view their bot status

   - [ ] Configuration Management
     * Bot settings form
     * Posting schedule setup
     * API key management
     * Success Criteria: Clients can configure their bots

   - [ ] Activity Monitoring
     * Tweet history view
     * Error reporting
     * Usage statistics
     * Success Criteria: Clients can monitor bot activity

2. Core Engine Features (MVP)
   - [ ] Simple Scheduler
     * Basic time-based scheduling
     * Round-robin client rotation
     * Success Criteria: Tweets post on schedule

   - [ ] Tweet Generation
     * OpenAI integration
     * Basic prompt handling
     * Success Criteria: Generates appropriate tweets

   - [ ] Tweet Posting
     * Twitter API integration
     * Status tracking
     * Success Criteria: Tweets post successfully

3. Basic Monitoring (MVP)
   - [ ] Error Logging
     * File-based logging
     * Error surfacing in UI
     * Success Criteria: Issues are visible and trackable

   - [ ] Usage Tracking
     * API call counting
     * Rate limit monitoring
     * Success Criteria: Usage stays within limits

### Post-MVP Backlog 📋
1. Advanced UI Features
   - Analytics dashboard
   - Prompt management interface
   - User management system
   - Advanced configuration options

2. Performance Optimization
   - Multi-threading support
   - Advanced scheduling
   - Caching improvements
   - A/B testing framework

3. Enhanced Monitoring
   - Prometheus integration
   - Grafana dashboards
   - Advanced alerting
   - Detailed analytics

## Key Challenges and Analysis
1. Twitter API Integration
   - Need to obtain Twitter Developer Account access
   - Define required permission scopes
   - Implement rate limiting and error handling

2. Production Readiness
   - Need to implement comprehensive monitoring
   - Set up alerting for critical failures
   - Define backup and recovery procedures
   - Document deployment process

3. Security Considerations
   - API key management in production
   - Client data isolation
   - Rate limiting and quota management
   - Audit logging

## High-level Task Breakdown
1. Complete OpenAI Integration
   - [ ] Implement rate limiting
   - [ ] Add cost monitoring
   - [ ] Set up A/B testing framework
   - Success Criteria: All OpenAI-related tests passing, rate limits respected

2. Twitter Integration
   - [ ] Set up Twitter Developer Account
   - [ ] Implement Twitter client
   - [ ] Add tweet posting functionality
   - [ ] Implement rate limiting
   - Success Criteria: Successful tweet posting with proper error handling

3. Main Engine Loop
   - [ ] Design scheduler system
   - [ ] Implement client coordination
   - [ ] Add monitoring and metrics
   - [ ] Create recovery procedures
   - Success Criteria: Engine running continuously without manual intervention

4. Production Setup
   - [ ] Create Docker configuration
   - [ ] Set up monitoring stack
   - [ ] Configure backup system
   - [ ] Document deployment process
   - Success Criteria: Successful deployment with monitoring

## Questions for Stakeholders
1. What are the expected rate limits per client?
2. What monitoring metrics are most critical?
3. What is the expected scale for the initial deployment?
4. What are the recovery time objectives (RTO) and recovery point objectives (RPO)? 