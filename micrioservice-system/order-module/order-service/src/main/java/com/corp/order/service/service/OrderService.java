package com.corp.order.service.service;

import java.util.Map;

/**
 * 订单Service接口
 */
public interface OrderService {

    Long createOrder(Map<String, Object> orderMap);

    Map<String, Object> getOrderById(Long id);

    boolean cancelOrder(Long id);
}
