package com.corp.product.service.service;

import java.util.List;
import java.util.Map;

/**
 * 商品Service接口
 */
public interface ProductService {

    Map<String, Object> getProductById(Long id);

    Long createProduct(Map<String, Object> productMap);

    boolean updateProduct(Long id, Map<String, Object> productMap);

    boolean deleteProduct(Long id);

    List<Map<String, Object>> searchProducts(String keyword, int page, int size);
}
