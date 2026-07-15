package com.corp.order.service.controller;

import com.corp.base.common.result.Result;
import com.corp.order.service.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 订单Controller
 * 提供创建/查询/取消订单接口
 */
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @Autowired
    private OrderService orderService;

    @PostMapping
    public Result<Long> createOrder(@RequestBody Map<String, Object> orderMap) {
        return Result.success(orderService.createOrder(orderMap));
    }

    @GetMapping("/{id}")
    public Result<Map<String, Object>> getOrderById(@PathVariable Long id) {
        return Result.success(orderService.getOrderById(id));
    }

    @PutMapping("/{id}/cancel")
    public Result<Boolean> cancelOrder(@PathVariable Long id) {
        return Result.success(orderService.cancelOrder(id));
    }
}
