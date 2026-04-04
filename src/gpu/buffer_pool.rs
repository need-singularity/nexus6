use std::sync::Mutex;

/// Simple buffer pool for reusing Vec<f32> allocations.
/// Avoids repeated heap allocation in hot loops.
pub struct BufferPool {
    pool: Mutex<Vec<Vec<f32>>>,
    default_capacity: usize,
}

impl BufferPool {
    /// Create a new pool. `default_capacity` is the initial Vec capacity for new buffers.
    pub fn new(default_capacity: usize) -> Self {
        Self {
            pool: Mutex::new(Vec::new()),
            default_capacity,
        }
    }

    /// Get a buffer from the pool, or allocate a new one.
    /// The returned buffer is cleared (len=0) but retains its capacity.
    pub fn get(&self) -> Result<Vec<f32>, String> {
        let mut pool = self.pool.lock().map_err(|e| format!("BufferPool lock poisoned: {e}"))?;
        match pool.pop() {
            Some(mut buf) => {
                buf.clear();
                Ok(buf)
            }
            None => Ok(Vec::with_capacity(self.default_capacity)),
        }
    }

    /// Return a buffer to the pool for reuse.
    pub fn put(&self, buf: Vec<f32>) -> Result<(), String> {
        let mut pool = self.pool.lock().map_err(|e| format!("BufferPool lock poisoned: {e}"))?;
        pool.push(buf);
        Ok(())
    }

    /// Number of buffers currently in the pool.
    pub fn available(&self) -> Result<usize, String> {
        let pool = self.pool.lock().map_err(|e| format!("BufferPool lock poisoned: {e}"))?;
        Ok(pool.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pool_reuse() {
        let pool = BufferPool::new(1024);
        assert_eq!(pool.available().unwrap(), 0);

        let mut buf = pool.get().unwrap();
        buf.extend_from_slice(&[1.0, 2.0, 3.0]);
        assert!(buf.capacity() >= 1024);

        pool.put(buf).unwrap();
        assert_eq!(pool.available().unwrap(), 1);

        let buf2 = pool.get().unwrap();
        assert_eq!(buf2.len(), 0); // cleared
        assert!(buf2.capacity() >= 1024); // capacity retained
        assert_eq!(pool.available().unwrap(), 0);
    }
}
