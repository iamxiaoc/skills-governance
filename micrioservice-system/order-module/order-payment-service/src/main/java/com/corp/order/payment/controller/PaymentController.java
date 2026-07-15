package com.corp.order.payment.controller;

import com.corp.base.common.result.Result;
import com.corp.order.payment.service.PaymentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 支付Controller
 * 提供发起支付/查询支付状态/退款接口
 */
@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    @Autowired
    private PaymentService paymentService;

    @PostMapping
    public Result<Map<String, String>> createPayment(@RequestBody Map<String, Object> paymentMap) {
        return Result.success(paymentService.createPayment(paymentMap));
    }

    @GetMapping("/{paymentId}")
    public Result<Map<String, Object>> getPaymentStatus(@PathVariable String paymentId) {
        return Result.success(paymentService.getPaymentStatus(paymentId));
    }

    @PostMapping("/{paymentId}/refund")
    public Result<Boolean> refund(@PathVariable String paymentId, @RequestBody Map<String, Object> refundMap) {
        return Result.success(paymentService.refund(paymentId, refundMap));
    }
}
