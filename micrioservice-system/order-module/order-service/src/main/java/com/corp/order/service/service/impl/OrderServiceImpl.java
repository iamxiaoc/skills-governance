package com.corp.order.service.service.impl;

import com.corp.id.IdGenerator;
import com.corp.id.IdGeneratorFactory;
import com.corp.monitor.MonitorUtils;
import com.corp.order.framework.handler.OrderTypeHandler;
import com.corp.order.framework.mq.OrderMessageProducer;
import com.corp.order.service.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * OrderService实现类
 */
@Service
public class OrderServiceImpl implements OrderService {

    @Autowired
    private OrderMessageProducer orderMessageProducer;

    private IdGenerator idGenerator = IdGeneratorFactory.getDefault();

    @Override
    public Long createOrder(Map<String, Object> orderMap) {
        // 简化版：实际应入库并生成订单ID
        Long orderId = idGenerator.nextBizId("ORD");
        int orderType = (Integer) orderMap.getOrDefault("type", 1);
        OrderTypeHandler.getHandler(orderType).handle(orderId, orderType);
        orderMessageProducer.sendOrderCreateMessage(orderId, orderMap.toString());
        MonitorUtils.increment("order.create.count");
        return orderId;
    }

    @Override
    public Map<String, Object> getOrderById(Long id) {
        // 简化版：实际应查询数据库
        Map<String, Object> orderMap = new HashMap<>();
        orderMap.put("id", id);
        orderMap.put("status", "CREATED");
        return orderMap;
    }

    @Override
    public boolean cancelOrder(Long id) {
        // 简化版：实际应更新订单状态
        orderMessageProducer.sendOrderStatusChangeMessage(id, 1, 5);
        MonitorUtils.increment("order.cancel.count");
        return true;
    }
}
