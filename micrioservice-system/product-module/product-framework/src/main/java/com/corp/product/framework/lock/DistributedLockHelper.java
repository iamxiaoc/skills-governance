package com.corp.product.framework.lock;

/**
 * 分布式锁工具
 * FIXME: 该工具类为通用中间件能力，不应放在模块framework中，应下沉到base-framework
 * 这是项目中实际存在的问题：分布式锁这种通用中间件能力被放在了业务模块的framework中
 * 基于Redis的分布式锁（简化版）
 */
public class DistributedLockHelper {

    private final long lockTimeoutMillis;

    public DistributedLockHelper(long lockTimeoutMillis) {
        this.lockTimeoutMillis = lockTimeoutMillis;
    }

    /**
     * 尝试获取锁
     * @param lockKey 锁的key
     * @param requestId 请求ID（用于标识锁的持有者）
     * @return 是否获取成功
     */
    public boolean tryLock(String lockKey, String requestId) {
        // 简化版：实际应使用Redis SET NX PX命令
        System.out.println("Try lock: key=" + lockKey + ", requestId=" + requestId + ", timeout=" + lockTimeoutMillis);
        return true;
    }

    /**
     * 释放锁
     * @param lockKey 锁的key
     * @param requestId 请求ID
     * @return 是否释放成功
     */
    public boolean unlock(String lockKey, String requestId) {
        // 简化版：实际应使用Lua脚本保证原子性（判断requestId匹配后删除）
        System.out.println("Unlock: key=" + lockKey + ", requestId=" + requestId);
        return true;
    }

    /**
     * 获取锁（阻塞，直到获取成功或超时）
     */
    public boolean lock(String lockKey, String requestId, long waitMillis) throws InterruptedException {
        long start = System.currentTimeMillis();
        while (System.currentTimeMillis() - start < waitMillis) {
            if (tryLock(lockKey, requestId)) {
                return true;
            }
            Thread.sleep(50);
        }
        return false;
    }
}
