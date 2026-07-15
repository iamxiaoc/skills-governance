package com.corp.product.framework.es;

import com.corp.monitor.MonitorUtils;
import com.corp.trace.TraceContext;

/**
 * 商品ES索引工具（业务相关）
 * 处理商品搜索索引的创建和同步
 */
public class ProductIndexHelper {

    private final String indexName;

    public ProductIndexHelper(String indexName) {
        this.indexName = indexName;
    }

    /**
     * 创建商品索引
     */
    public boolean createIndex() {
        // 简化版：实际应调用Elasticsearch API创建索引
        System.out.println("Create product index: " + indexName);
        return true;
    }

    /**
     * 同步商品数据到ES
     */
    public boolean syncProduct(Long productId, String productData) {
        // 简化版：实际应调用Elasticsearch API索引文档
        String traceId = TraceContext.getTraceId();
        System.out.println("Sync product to ES: index=" + indexName + ", productId=" + productId + ", traceId=" + traceId);
        MonitorUtils.increment("es.product.sync");
        return true;
    }

    /**
     * 删除商品索引
     */
    public boolean deleteProduct(Long productId) {
        System.out.println("Delete product from ES: index=" + indexName + ", productId=" + productId);
        return true;
    }
}
