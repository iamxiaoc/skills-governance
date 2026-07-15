package com.corp.order.framework.datasource;

/**
 * 订单分库分表策略
 * FIXME: 该工具类为通用中间件能力，不应放在模块framework中，应下沉到base-framework
 * 这是项目中实际存在的问题：分库分表这种通用中间件能力被放在了业务模块的framework中
 */
public class OrderShardingStrategy {

    private final int dbCount;
    private final int tableCount;

    public OrderShardingStrategy(int dbCount, int tableCount) {
        this.dbCount = dbCount;
        this.tableCount = tableCount;
    }

    /**
     * 根据订单ID计算分库位置
     */
    public int getDbIndex(Long orderId) {
        return (int) (orderId % dbCount);
    }

    /**
     * 根据订单ID计算分表位置
     */
    public int getTableIndex(Long orderId) {
        return (int) (orderId / dbCount % tableCount);
    }

    /**
     * 根据用户ID计算分库位置（用于按用户查询订单）
     */
    public int getDbIndexByUserId(Long userId) {
        return (int) (userId % dbCount);
    }

    /**
     * 根据用户ID计算分表位置
     */
    public int getTableIndexByUserId(Long userId) {
        return (int) (userId / dbCount % tableCount);
    }
}
