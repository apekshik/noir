// Example of transitioning from read to write lock
shared userSessions: [String: Session] = []
shared sessionCount: Int = 0

async func extendSession(sessionId: String) -> Bool:
    // First check if session exists with read lock
    grab userSessions to read:
        if !userSessions.hasKey(sessionId):
            return false
        ::
        
        session: Session = userSessions[sessionId]
        if session.isExpired():
            // Need to switch to write lock to remove expired session
            grab userSessions to write:
                userSessions.remove(sessionId)
                sessionCount = sessionCount - 1
                return false
            ::
        ::
        
        // Session is valid, need write lock to extend it
        grab userSessions to write:
            userSessions[sessionId].extendExpiry()
            return true
        ::
    ::
::

// Cache eviction example
shared cache: [String: CacheEntry] = []
shared evictionStats: {
    evictionCount: Int = 0,
    lastEvictionTime: Time = now()
}

async func evictStaleEntries() -> Int:
    staleKeys: [String] = []
    
    // First scan for stale entries with read lock
    grab cache to read:
        for key, entry in cache:
            if entry.isStale():
                staleKeys.append(key)
            ::
        ::
        
        if staleKeys.length == 0:
            return 0
        ::
    ::
    
    // Then remove them with write lock
    grab cache to write, evictionStats to write:
        for key in staleKeys:
            cache.remove(key)
        ::
        evictionStats.evictionCount += staleKeys.length
        evictionStats.lastEvictionTime = now()
        return staleKeys.length
    ::
::

// Resource pool with preemption
shared resourcePool: [Resource] = []
shared highPriorityQueue: [Task] = []

async func processHighPriorityTask(task: Task) -> Bool:
    // Check resource availability with read lock
    grab resourcePool to read, highPriorityQueue to read:
        if resourcePool.length > 0:
            // Resources available, switch to write lock to grab one
            grab resourcePool to write:
                resource: Resource = resourcePool.pop()
                processTaskWithResource(task, resource)
                return true
            ::
        :: else if highPriorityQueue.length < MAX_QUEUE_SIZE:
            // No resources, queue task if space available
            grab highPriorityQueue to write:
                highPriorityQueue.push(task)
                return true
            ::
        ::
    ::
    
    return false
::